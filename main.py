import os
import sys
import cv2
import numpy as np
from OpenGL.raw.GLUT import glutPostRedisplay
from cvzone.HandTrackingModule import HandDetector
from monitor import SystemMonitor  # system-level CPU/RAM logger

import threading
import queue
import time

from src.controllers.hand_controller import HandTrackingController
from src.rendering.cube_renderer import CubeRenderer


global_mode = {"mode": 3}   # 1=RAW, 2=SMOOTH, 3=KALMAN


def resource_path(rel_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(".")
    return os.path.join(base, rel_path)


def main():
    # ================== START SYSTEM MONITOR ==================
    monitor = SystemMonitor(
        interval_sec=1.0,
        csv_path="system_benchmark.csv"
    )
    monitor.start()
    # ==========================================================

    try:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        width = 1280
        height = 720
        cx = width / 2.0
        cy = height / 2.0

        detector = HandDetector(detectionCon=0.8, maxHands=2)

        rot_ctrl = HandTrackingController()
        rot_ctrl.set_mode(3)

        scale = 1.0
        scale_alpha = 0.2
        baseline_left_pos = None
        last_baseline_time = time.time()
        baseline_interval = 1.0

        rot_x = 0.0
        rot_y = 0.0

        rot_dx_s = 0.0
        rot_dy_s = 0.0

        render_queue = queue.Queue()

        obj_path = resource_path("models/gathered-anatomy/right_hand.obj")
        cube = CubeRenderer(obj_path=obj_path)

        def gl_thread():
            from OpenGL.GLUT import (
                glutInit, glutInitDisplayMode, glutInitWindowSize,
                glutCreateWindow, glutDisplayFunc, glutIdleFunc, glutMainLoop,
                glutKeyboardFunc,
                GLUT_DOUBLE, GLUT_RGBA, GLUT_DEPTH
            )

            glutInit()
            glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
            glutInitWindowSize(800, 600)
            glutCreateWindow(b"3D Object")

            cube.initgl(800, 600)

            def display():
                try:
                    rx, ry, sc = render_queue.get_nowait()
                    cube.updatestate(rx, ry, sc)
                except queue.Empty:
                    pass
                cube.draw()
                glutPostRedisplay()

            def keyboard(key, x, y):
                k = key.decode("utf-8")
                if k == '1':
                    global_mode["mode"] = 1
                    print("Mode rotation: RAW")
                elif k == '2':
                    global_mode["mode"] = 2
                    rot_ctrl.set_mode(2)
                    print("Mode rotation: SMOOTH")
                elif k == '3':
                    global_mode["mode"] = 3
                    rot_ctrl.set_mode(3)
                    print("Mode rotation: KALMAN")
                elif k == 'q' or ord(k) == 27:
                    print("Exit requested")
                    sys.exit(0)

            glutDisplayFunc(display)
            glutIdleFunc(display)
            glutKeyboardFunc(keyboard)
            glutMainLoop()

        threading.Thread(target=gl_thread, daemon=True).start()

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            img = cv2.flip(frame, 1)
            hands, img = detector.findHands(img, flipType=False)

            rot_vector = (0.0, 0.0)
            now = time.time()
            mode_rot = global_mode["mode"]

            if hands:
                hands = sorted(hands, key=lambda h: h['center'][0])

                # kiri = rotasi
                if len(hands) >= 1:
                    left = hands[0]
                    x_raw, y_raw = left['center']

                    if mode_rot == 1:          # RAW
                        x_f, y_f = float(x_raw), float(y_raw)
                    else:
                        x_f, y_f = rot_ctrl.process(float(x_raw), float(y_raw))

                    cv2.circle(img, (int(x_raw), int(y_raw)), 7, (0, 0, 255), -1)
                    cv2.circle(img, (int(x_f), int(y_f)), 7, (0, 255, 0), 2)

                    if mode_rot == 1:
                        # RAW: pakai posisi absolut
                        rot_vector = (x_f, y_f)
                    else:
                        if baseline_left_pos is None:
                            baseline_left_pos = (x_f, y_f)

                        dx = x_f - baseline_left_pos[0]
                        dy = y_f - baseline_left_pos[1]
                        rot_vector = (dx, dy)

                        cv2.circle(
                            img,
                            (int(baseline_left_pos[0]), int(baseline_left_pos[1])),
                            7, (255, 0, 0), 2
                        )
                        cv2.line(
                            img,
                            (int(baseline_left_pos[0]), int(baseline_left_pos[1])),
                            (int(x_f), int(y_f)),
                            (255, 0, 0), 1
                        )

                        if now - last_baseline_time > baseline_interval:
                            baseline_left_pos = (x_f, y_f)
                            last_baseline_time = now

                # kanan = scale
                if len(hands) >= 2:
                    right = hands[1]
                    lmR = right['lmList']
                    x_thumb, y_thumb, _ = lmR[4]
                    x_idx, y_idx, _ = lmR[8]

                    dist = np.hypot(x_idx - x_thumb, y_idx - y_thumb)

                    # hanya batas bawah jarak (supaya tidak 0)
                    d_min = 30.0
                    d_clamped = max(d_min, dist)

                    # batas bawah skala
                    s_min = 0.5
                    # sensitivitas pembesaran
                    k = 1.0 / (200.0 - d_min)

                    t_delta = (d_clamped - d_min)
                    target_scale = s_min + k * t_delta  # tidak ada limit atas

                    if mode_rot == 1:
                        scale = target_scale
                    else:
                        scale = (1 - scale_alpha) * scale + scale_alpha * target_scale

                    cv2.line(
                        img, (int(x_thumb), int(y_thumb)),
                        (int(x_idx), int(y_idx)), (255, 0, 0), 2
                    )
                    cv2.putText(
                        img, f"dist={int(dist)} scale={scale:.2f}",
                        (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 255), 2
                    )
            else:
                baseline_left_pos = None

            # mapping / integrasi rotasi
            dx, dy = rot_vector

            if mode_rot == 1:
                # RAW: perkuat jitter dekat tengah
                x_norm = (dx - cx) / cx       # -1..1
                y_norm = (dy - cy) / cy       # -1..1

                jitter_gain = 180.0
                x_nonlin = np.sign(x_norm) * (abs(x_norm) ** 0.5)
                y_nonlin = np.sign(y_norm) * (abs(y_norm) ** 0.5)

                rot_x = -y_nonlin * jitter_gain
                rot_y =  x_nonlin * jitter_gain
            else:
                alpha = 0.3
                rot_dx_s = (1 - alpha) * rot_dx_s + alpha * dx
                rot_dy_s = (1 - alpha) * rot_dy_s + alpha * dy

                dead = 1.0
                dx_eff = 0.0 if abs(rot_dx_s) < dead else rot_dx_s
                dy_eff = 0.0 if abs(rot_dy_s) < dead else rot_dy_s
                gain = 0.04

                rot_x += -dy_eff * gain
                rot_y +=  dx_eff * gain

            if render_queue.empty():
                render_queue.put((rot_x, rot_y, scale))

            t_left = baseline_interval - (now - last_baseline_time)
            mode_name = {1: "RAW", 2: "SMOOTH", 3: "KALMAN"}.get(mode_rot, "UNK")

            cv2.putText(
                img,
                f"Rot vec: ({rot_vector[0]:.1f},{rot_vector[1]:.1f}) | Reset in {t_left:.1f}s",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2
            )

            cv2.putText(
                img,
                f"rot_x={rot_x:.2f} rot_y={rot_y:.2f} scale={scale:.2f} mode={mode_name}",
                (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 255, 0), 2
            )

            cv2.putText(
                img,
                "Left: rotation (1=RAW,2=Smooth,3=Kalman)  |  Right: scale",
                (20, img.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (200, 200, 200), 2
            )

            cv2.imshow("Two-Hand Control (Rotation + Scale)", img)

            if cv2.waitKey(1) == 27:
                break

        cap.release()
        cv2.destroyAllWindows()

    finally:
        monitor.stop()

if __name__ == "__main__":
    main()
