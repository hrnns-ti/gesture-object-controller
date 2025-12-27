from typing import Dict

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image

from .obj_loader import OBJLoader


class CubeRenderer:
    def __init__(self, obj_path: str | None = None):
        self.rotx: float = 0.0
        self.roty: float = 0.0
        self.scale: float = 4.0  # default, nanti dikali gesture

        # display list id
        self.gllist: int | None = None

        # geometry
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[list[int]] = []
        self.facecolors: list[tuple[float, float, float]] = []
        self.facenormals: list[tuple[float, float, float]] = []

        # texturing data
        self.texcoords: list[tuple[float, float]] = []
        self.facetexcoords: list[list[int]] = []
        self.facematerials: list[str | None] = []

        # material -> texture path (dari OBJLoader)
        self.materialtexturepaths: Dict[str, str] = {}
        # material -> OpenGL texture id (dibuat di initgl)
        self.materialtextures: Dict[str, int] = {}

        if obj_path is not None:
            loader = OBJLoader(obj_path)

            cx, cy, cz = loader.computecentroid()
            print(f"[CubeRenderer] CENTROID: ({cx:.2f}, {cy:.2f}, {cz:.2f})")

            # geser vertex supaya pusat objek di (0,0,0)
            self.vertices = [
                (v[0] - cx, v[1] - cy, v[2] - cz) for v in loader.vertices
            ]
            self.faces = loader.faces
            self.facecolors = loader.facecolors
            self.facenormals = loader.facenormals
            self.texcoords = loader.texcoords
            self.facetexcoords = loader.facetexcoords
            self.facematerials = loader.facematerials
            self.materialtexturepaths = loader.materialtexturepaths

            print("[CubeRenderer] vertices shifted by centroid")
            print(
                f"[CubeRenderer] mesh loaded: "
                f"{len(self.vertices)} vertices, {len(self.faces)} faces"
            )
        else:
            # fallback cube
            self.vertices = [
                (-1, -1, -1),
                (1, -1, -1),
                (1, 1, -1),
                (-1, 1, -1),
                (-1, -1, 1),
                (1, -1, 1),
                (1, 1, 1),
                (-1, 1, 1),
            ]
            self.faces = [
                [0, 1, 2, 3],
                [4, 5, 6, 7],
                [0, 1, 5, 4],
                [2, 3, 7, 6],
                [1, 2, 6, 5],
                [0, 3, 7, 4],
            ]
            self.facecolors = [(0.7, 0.7, 1.0)] * len(self.faces)
            self.facenormals = [(0.0, 0.0, 1.0)] * len(self.faces)
            self.texcoords = []
            self.facetexcoords = []
            self.facematerials = [None] * len(self.faces)
            print(
                f"[CubeRenderer] mesh loaded: {len(self.vertices)} vertices, "
                f"{len(self.faces)} faces"
            )

    def updatestate(self, rotx: float, roty: float, scale: float) -> None:
        self.rotx = rotx
        self.roty = roty
        self.scale = scale * 4.0

    def initgl(self, width: int = 800, height: int = 600) -> None:
        print("[CubeRenderer] init_gl")

        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)

        # lighting halus
        # glEnable(GL_LIGHTING)
        # glEnable(GL_LIGHT0)
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        # glLightfv(GL_LIGHT0, GL_POSITION,  (15.0, 15.0, 20.0, 1.0))
        # glLightfv(GL_LIGHT0, GL_DIFFUSE,   (1.3, 1.3, 1.3, 1.0))
        # glLightfv(GL_LIGHT0, GL_AMBIENT,   (0.45, 0.45, 0.45, 1.0))
        # glLightfv(GL_LIGHT0, GL_SPECULAR,  (0.0, 0.0, 0.0, 1.0))

        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glDisable(GL_CULL_FACE)

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(width) / float(height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # ---------- BUILD TEXTURES ----------
        self.materialtextures = {}
        for name, texpath in self.materialtexturepaths.items():
            if not os.path.exists(texpath):
                print(f"[CubeRenderer] texture not found: {texpath}")
                continue
            try:
                img = Image.open(texpath).convert("RGBA")
                w, h = img.size
                data = img.tobytes("raw", "RGBA", 0, -1)

                texid = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texid)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexImage2D(
                    GL_TEXTURE_2D,
                    0,
                    GL_RGBA,
                    w,
                    h,
                    0,
                    GL_RGBA,
                    GL_UNSIGNED_BYTE,
                    data,
                )
                self.materialtextures[name] = texid
                print(f"[CubeRenderer] texture loaded {texpath} -> id {texid}")
            except Exception as e:
                print(f"[CubeRenderer] failed to build texture {texpath}: {e}")

        if self.materialtextures:
            glEnable(GL_TEXTURE_2D)
        else:
            glDisable(GL_TEXTURE_2D)

        if self.gllist is not None:
            glDeleteLists(self.gllist, 1)
        self.gllist = glGenLists(1)

        glNewList(self.gllist, GL_COMPILE)

        current_texid = None
        if self.materialtextures:
            current_texid = next(iter(self.materialtextures.values()))
            glBindTexture(GL_TEXTURE_2D, current_texid)

        glBegin(GL_TRIANGLES)
        for face_idx, (verts, normal) in enumerate(
            zip(self.faces, self.facenormals)
        ):
            if len(verts) < 3:
                continue

            glColor3f(1.0, 1.0, 1.0)
            glNormal3f(*normal)

            uvidx_list = (
                self.facetexcoords[face_idx]
                if face_idx < len(self.facetexcoords)
                else []
            )

            v0 = verts[0]
            for i in range(1, len(verts) - 1):
                v1 = verts[i]
                v2 = verts[i + 1]

                for j, vidx in enumerate((v0, v1, v2)):
                    uvidx = uvidx_list[j] if len(uvidx_list) > j else -1
                    x, y, z = self.vertices[vidx]
                    if 0 <= uvidx < len(self.texcoords):
                        u, v = self.texcoords[uvidx]
                        glTexCoord2f(u, v)
                    glVertex3f(x, y, z)
        glEnd()

        glEndList()

        # cek error SETELAH display list selesai
        err = glGetError()
        if err != GL_NO_ERROR:
            print("[CubeRenderer] GL error after building display list:", err)

    def draw(self) -> None:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(
            0.0, 0.0, 8.5,
            0.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
        )

        glScalef(self.scale, self.scale, self.scale)
        glRotatef(self.rotx, 1.0, 0.0, 0.0)
        glRotatef(self.roty, 0.0, 1.0, 0.0)

        if self.materialtextures:
            glEnable(GL_TEXTURE_2D)
        else:
            glDisable(GL_TEXTURE_2D)

        if self.gllist is not None:
            glCallList(self.gllist)

        glutSwapBuffers()