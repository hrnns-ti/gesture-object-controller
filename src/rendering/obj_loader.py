import os
from typing import List, Tuple, Dict, Optional


class OBJLoader:
    def __init__(self, path: str):
        # posisi vertex
        self.vertices: List[Tuple[float, float, float]] = []
        # UV per-vertex
        self.texcoords: List[Tuple[float, float]] = []
        # tiap face: list indeks vertex (v0, v1, v2, ...)
        self.faces: List[List[int]] = []
        # tiap face: list indeks UV (sama panjang dengan faces[i]), -1 artinya tidak ada UV
        self.facetexcoords: List[List[int]] = []
        # warna per-face (fallback jika tidak ada tekstur)
        self.facecolors: List[Tuple[float, float, float]] = []
        # normal per-face
        self.facenormals: List[Tuple[float, float, float]] = []
        # nama material per-face
        self.facematerials: List[Optional[str]] = []
        # materialname -> warna Kd
        self.mtlcolors: Dict[str, Tuple[float, float, float]] = {}
        # materialname -> path file tekstur (map_Kd)
        self.materialtexturepaths: Dict[str, str] = {}

        # load OBJ + MTL
        self.load(path)

        # penamaan texture
        obj_basename = os.path.splitext(os.path.basename(path))[0]
        default_tex = obj_basename + ".jpg"
        basedir = os.path.dirname(path)

        # antisipasi map_Kd
        if not self.materialtexturepaths and self.mtlcolors:
            for mat_name in self.mtlcolors.keys():
                self.materialtexturepaths[mat_name] = os.path.join(basedir, default_tex)
            print(f"[OBJLoader] created default texture {default_tex} for materials: "
                  f"{list(self.mtlcolors.keys())}")
        else:
            # kalau sudah ada map_Kd
            if self.materialtexturepaths:
                print(f"[OBJLoader] overriding texture names to {default_tex}")
                for mat_name in list(self.materialtexturepaths.keys()):
                    self.materialtexturepaths[mat_name] = os.path.join(basedir, default_tex)

    def load(self, path: str) -> None:
        basedir = os.path.dirname(path)
        current_color: Tuple[float, float, float] = (0.8, 0.8, 0.8)
        current_material: Optional[str] = None

        with open(path, "r") as f:
            lines = f.readlines()

        # 1) cari dan load .mtl kalau ada
        for line in lines:
            line = line.strip()
            if line.startswith("mtllib "):
                _, mtlname = line.split(maxsplit=1)
                mtlpath = os.path.join(basedir, mtlname)
                self.loadmtl(mtlpath, basedir)
                break

        # 2) parse vertex, UV, dan face
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # ganti material aktif
            if line.startswith("usemtl "):
                _, matname = line.split(maxsplit=1)
                current_material = matname.strip()
                current_color = self.mtlcolors.get(current_material, (0.8, 0.8, 0.8))

            # vertex posisi
            elif line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    x, y, z = parts[1:4]
                    self.vertices.append((float(x), float(y), float(z)))

            # UV koordinat
            elif line.startswith("vt "):
                parts = line.split()
                if len(parts) >= 3:
                    u, v = parts[1:3]
                    self.texcoords.append((float(u), float(v)))

            # face bisa 3,4,5,... vertex
            elif line.startswith("f "):
                parts = line.split()[1:]
                vidx_list: List[int] = []
                tidx_list: List[int] = []

                for p in parts:
                    # format umum: v / v/vt / v/vt/vn
                    items = p.split("/")
                    # index vertex (OBJ index mulai 1)
                    vidx = int(items[0]) - 1
                    vidx_list.append(vidx)

                    # index UV kalau ada
                    if len(items) >= 2 and items[1] != "":
                        tidx = int(items[1]) - 1
                        tidx_list.append(tidx)
                    else:
                        tidx_list.append(-1)  # tidak ada UV

                if len(vidx_list) >= 3:
                    self.faces.append(vidx_list)
                    self.facetexcoords.append(tidx_list)
                    self.facecolors.append(current_color)
                    self.facematerials.append(current_material)

                    # hitung normal dari 3 vertex pertama
                    v0 = self.vertices[vidx_list[0]]
                    v1 = self.vertices[vidx_list[1]]
                    v2 = self.vertices[vidx_list[2]]
                    nx, ny, nz = self.computenormal(v0, v1, v2)
                    self.facenormals.append((nx, ny, nz))

        print(
            f"[OBJLoader] loaded {len(self.vertices)} vertices, "
            f"{len(self.faces)} faces, {len(self.mtlcolors)} materials, "
            f"{len(self.materialtexturepaths)} texture paths"
        )

    def loadmtl(self, mtlpath: str, basedir: str) -> None:
        if not os.path.exists(mtlpath):
            print(f"[OBJLoader] MTL not found: {mtlpath}")
            return

        current_name: Optional[str] = None

        with open(mtlpath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("newmtl "):
                    _, name = line.split(maxsplit=1)
                    current_name = name.strip()

                elif line.startswith("Kd ") and current_name is not None:
                    parts = line.split()
                    if len(parts) >= 4:
                        r, g, b = parts[1:4]
                        self.mtlcolors[current_name] = (
                            float(r),
                            float(g),
                            float(b),
                        )

                elif line.startswith("map_Kd ") and current_name is not None:
                    parts = line.split()
                    if len(parts) >= 2:
                        texname = parts[1]
                        texpath = os.path.join(basedir, texname)
                        self.materialtexturepaths[current_name] = texpath

        print(
            f"[OBJLoader] loaded {len(self.mtlcolors)} mtl colors, "
            f"{len(self.materialtexturepaths)} texture paths from {mtlpath}"
        )

    # ---------- UTILITAS ----------
    def computenormal(
        self,
        v0: Tuple[float, float, float],
        v1: Tuple[float, float, float],
        v2: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        """Normal face dari tiga titik v0,v1,v2."""
        x1, y1, z1 = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
        x2, y2, z2 = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]

        nx = y1 * z2 - z1 * y2
        ny = z1 * x2 - x1 * z2
        nz = x1 * y2 - y1 * x2

        length = (nx * nx + ny * ny + nz * nz) ** 0.5
        if length == 0.0:
            return (0.0, 0.0, 1.0)
        return (nx / length, ny / length, nz / length)

    def computecentroid(self) -> Tuple[float, float, float]:
        """Titik tengah (centroid) semua vertex."""
        if not self.vertices:
            return (0.0, 0.0, 0.0)
        sx = sum(v[0] for v in self.vertices)
        sy = sum(v[1] for v in self.vertices)
        sz = sum(v[2] for v in self.vertices)
        n = len(self.vertices)
        return (sx / n, sy / n, sz / n)
