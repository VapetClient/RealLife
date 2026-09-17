"""
Generate an anatomically proportioned stylized 3D human mannequin / character mesh in OBJ, MTL, and GLTF format.
The model features:
- Head with facial feature suggestions (nose, eye sockets, chin, ears)
- Neck
- Torso: chest/pectoral definition, ribcage, waist, hips/pelvis
- Arms: shoulders (deltoids), upper arms (biceps/triceps), elbows, forearms, hands with thumb and fingers
- Legs: upper thighs (quadriceps/hamstrings), knees, calves/shins, ankles, feet with toes
- Symmetry, clean surface normals, UV mapping coordinates, and materials (skin, clothes/outfit or athletic wear, hair).
"""

import math
import json
import os

class Mesh:
    def __init__(self):
        self.vertices = []      # list of (x, y, z)
        self.normals = []       # list of (nx, ny, nz)
        self.uvs = []           # list of (u, v)
        # faces: list of (v_indices, uv_indices, material_name)
        # v_indices is list of 3 or 4 vertex indices (0-based)
        self.faces = []

    def add_vertex(self, x, y, z):
        idx = len(self.vertices)
        self.vertices.append((float(x), float(y), float(z)))
        return idx

    def add_uv(self, u, v):
        idx = len(self.uvs)
        self.uvs.append((float(u), float(v)))
        return idx

    def add_triangle(self, v1, v2, v3, uv1=(0,0), uv2=(0,0), uv3=(0,0), mat="skin"):
        u1 = self.add_uv(*uv1)
        u2 = self.add_uv(*uv2)
        u3 = self.add_uv(*uv3)
        self.faces.append(([v1, v2, v3], [u1, u2, u3], mat))

    def add_quad(self, v1, v2, v3, v4, uv1=(0,0), uv2=(1,0), uv3=(1,1), uv4=(0,1), mat="skin"):
        u1 = self.add_uv(*uv1)
        u2 = self.add_uv(*uv2)
        u3 = self.add_uv(*uv3)
        u4 = self.add_uv(*uv4)
        # Split into 2 triangles
        self.faces.append(([v1, v2, v3], [u1, u2, u3], mat))
        self.faces.append(([v1, v3, v4], [u1, u3, u4], mat))

    def add_cylinder_segment(self, bottom_center, bottom_rx, bottom_rz,
                             top_center, top_rx, top_rz,
                             segments=16, mat="skin",
                             bottom_v_override=None, top_v_override=None):
        """Creates a truncated elliptical cylinder/frustum."""
        bx, by, bz = bottom_center
        tx, ty, tz = top_center

        b_indices = []
        t_indices = []

        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            if bottom_v_override:
                b_idx = bottom_v_override[i]
            else:
                b_idx = self.add_vertex(bx + cos_a * bottom_rx, by, bz + sin_a * bottom_rz)
            b_indices.append(b_idx)

            if top_v_override:
                t_idx = top_v_override[i]
            else:
                t_idx = self.add_vertex(tx + cos_a * top_rx, ty, tz + sin_a * top_rz)
            t_indices.append(t_idx)

        for i in range(segments):
            next_i = (i + 1) % segments
            u_left = i / segments
            u_right = (i + 1) / segments
            self.add_quad(b_indices[i], b_indices[next_i], t_indices[next_i], t_indices[i],
                          (u_left, 0.0), (u_right, 0.0), (u_right, 1.0), (u_left, 1.0),
                          mat=mat)

        return b_indices, t_indices

    def add_ellipsoid(self, center, rx, ry, rz, lat_bands=12, lon_bands=16, mat="skin"):
        cx, cy, cz = center
        grid = []
        for i in range(lat_bands + 1):
            theta = math.pi * i / lat_bands
            sin_t = math.sin(theta)
            cos_t = math.cos(theta)
            row = []
            for j in range(lon_bands):
                phi = 2.0 * math.pi * j / lon_bands
                sin_p = math.sin(phi)
                cos_p = math.cos(phi)

                x = cx + rx * sin_t * cos_p
                y = cy + ry * cos_t
                z = cz + rz * sin_t * sin_p
                v_idx = self.add_vertex(x, y, z)
                row.append(v_idx)
            grid.append(row)

        for i in range(lat_bands):
            for j in range(lon_bands):
                next_j = (j + 1) % lon_bands
                v1 = grid[i][j]
                v2 = grid[i][next_j]
                v3 = grid[i+1][next_j]
                v4 = grid[i+1][j]
                u1 = j / lon_bands
                u2 = (j + 1) / lon_bands
                v_top = 1.0 - (i / lat_bands)
                v_bot = 1.0 - ((i + 1) / lat_bands)
                self.add_quad(v1, v2, v3, v4,
                              (u1, v_top), (u2, v_top), (u2, v_bot), (u1, v_bot),
                              mat=mat)

    def add_capsule(self, p1, p2, radius1, radius2, segments=12, rings=4, mat="skin"):
        """Creates a smooth limb segment between p1 and p2."""
        x1, y1, z1 = p1
        x2, y2, z2 = p2
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length < 1e-6:
            return

        # Direction vector
        dir_x, dir_y, dir_z = dx / length, dy / length, dz / length

        # Arbitrary perpendicular vector
        if abs(dir_y) < 0.9:
            up_x, up_y, up_z = 0, 1, 0
        else:
            up_x, up_y, up_z = 1, 0, 0

        # Gram-Schmidt orthogonalization for orthonormal basis (u, v, dir)
        # dot product up . dir
        dot = up_x * dir_x + up_y * dir_y + up_z * dir_z
        ux = up_x - dot * dir_x
        uy = up_y - dot * dir_y
        uz = up_z - dot * dir_z
        u_len = math.sqrt(ux*ux + uy*uy + uz*uz)
        ux, uy, uz = ux/u_len, uy/u_len, uz/u_len

        # cross product dir x u
        vx = dir_y * uz - dir_z * uy
        vy = dir_z * ux - dir_x * uz
        vz = dir_x * uy - dir_y * ux

        rings_pts = []
        for r in range(rings + 1):
            t = r / rings
            cur_p = (x1 + dx * t, y1 + dy * t, z1 + dz * t)
            cur_r = radius1 + (radius2 - radius1) * t
            ring = []
            for s in range(segments):
                angle = 2.0 * math.pi * s / segments
                c = math.cos(angle)
                s_ang = math.sin(angle)
                px = cur_p[0] + (ux * c + vx * s_ang) * cur_r
                py = cur_p[1] + (uy * c + vy * s_ang) * cur_r
                pz = cur_p[2] + (uz * c + vz * s_ang) * cur_r
                ring.append(self.add_vertex(px, py, pz))
            rings_pts.append(ring)

        for r in range(rings):
            for s in range(segments):
                next_s = (s + 1) % segments
                v1 = rings_pts[r][s]
                v2 = rings_pts[r][next_s]
                v3 = rings_pts[r+1][next_s]
                v4 = rings_pts[r+1][s]
                u_left = s / segments
                u_right = (s + 1) / segments
                v_bot = r / rings
                v_top = (r + 1) / rings
                self.add_quad(v1, v2, v3, v4,
                              (u_left, v_bot), (u_right, v_bot), (u_right, v_top), (u_left, v_top),
                              mat=mat)

    def compute_vertex_normals(self):
        """Computes smooth vertex normals based on adjacent face normals."""
        normals = [[0.0, 0.0, 0.0] for _ in self.vertices]
        for f, _, _ in self.faces:
            v0 = self.vertices[f[0]]
            v1 = self.vertices[f[1]]
            v2 = self.vertices[f[2]]
            # Cross product (v1 - v0) x (v2 - v0)
            ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
            bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            norm = math.sqrt(nx*nx + ny*ny + nz*nz)
            if norm > 1e-8:
                nx /= norm
                ny /= norm
                nz /= norm
                for vid in f:
                    normals[vid][0] += nx
                    normals[vid][1] += ny
                    normals[vid][2] += nz

        self.normals = []
        for n in normals:
            length = math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
            if length > 1e-8:
                self.normals.append((n[0]/length, n[1]/length, n[2]/length))
            else:
                self.normals.append((0.0, 1.0, 0.0))

    def export_obj(self, filepath, mtl_filename="human.mtl"):
        self.compute_vertex_normals()
        with open(filepath, "w") as f:
            f.write("# Human 3D Model\n")
            f.write(f"mtllib {mtl_filename}\n\n")

            for v in self.vertices:
                f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")

            for vn in self.normals:
                f.write(f"vn {vn[0]:.4f} {vn[1]:.4f} {vn[2]:.4f}\n")

            for vt in self.uvs:
                f.write(f"vt {vt[0]:.4f} {vt[1]:.4f}\n")

            # Group faces by material
            by_mat = {}
            for verts, uvs, mat in self.faces:
                if mat not in by_mat:
                    by_mat[mat] = []
                by_mat[mat].append((verts, uvs))

            for mat, face_list in by_mat.items():
                f.write(f"\ng {mat}\nusemtl {mat}\ns 1\n")
                for verts, uvs in face_list:
                    # OBJ indices are 1-based: v/vt/vn
                    parts = []
                    for vi, ui in zip(verts, uvs):
                        parts.append(f"{vi+1}/{ui+1}/{vi+1}")
                    f.write("f " + " ".join(parts) + "\n")

    def export_gltf(self, filepath):
        """Export simple GLTF 2.0 (embedded buffers in base64 or separate bin)."""
        import struct
        import base64

        self.compute_vertex_normals()

        # Build combined vertex buffer: pos(3f), normal(3f), uv(2f)
        # Note: OBJ shares vertex list, but here we can export indexed triangles
        # Flattened faces
        positions = []
        normals = []
        texcoords = []
        indices = []

        vertex_map = {}
        for verts, uvs, mat in self.faces:
            for vi, ui in zip(verts, uvs):
                key = (vi, ui)
                if key not in vertex_map:
                    new_idx = len(positions) // 3
                    vertex_map[key] = new_idx
                    v = self.vertices[vi]
                    vn = self.normals[vi]
                    vt = self.uvs[ui]
                    positions.extend(v)
                    normals.extend(vn)
                    texcoords.extend(vt)
                indices.append(vertex_map[key])

        # Pack binary buffer
        # pos: floats, norm: floats, uv: floats, indices: uint16 or uint32
        pos_bytes = struct.pack(f"<{len(positions)}f", *positions)
        norm_bytes = struct.pack(f"<{len(normals)}f", *normals)
        uv_bytes = struct.pack(f"<{len(texcoords)}f", *texcoords)
        idx_type = "H" if max(indices) < 65535 else "I"
        idx_component_type = 5123 if idx_type == "H" else 5125
        idx_bytes = struct.pack(f"<{len(indices)}{idx_type}", *indices)

        # Pad to 4-byte boundaries
        def pad4(b):
            rem = len(b) % 4
            return b + (b"\x00" * (4 - rem)) if rem != 0 else b

        pos_bytes = pad4(pos_bytes)
        norm_bytes = pad4(norm_bytes)
        uv_bytes = pad4(uv_bytes)
        idx_bytes = pad4(idx_bytes)

        buffer_data = pos_bytes + norm_bytes + uv_bytes + idx_bytes
        b64_buffer = base64.b64encode(buffer_data).decode("ascii")

        pos_offset = 0
        norm_offset = len(pos_bytes)
        uv_offset = norm_offset + len(norm_bytes)
        idx_offset = uv_offset + len(uv_bytes)

        min_pos = [min(positions[i::3]) for i in range(3)]
        max_pos = [max(positions[i::3]) for i in range(3)]

        gltf = {
            "asset": {"version": "2.0", "generator": "Arena 3D Human Generator"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": "HumanCharacter"}],
            "meshes": [{
                "name": "HumanMesh",
                "primitives": [{
                    "attributes": {
                        "POSITION": 0,
                        "NORMAL": 1,
                        "TEXCOORD_0": 2
                    },
                    "indices": 3,
                    "material": 0
                }]
            }],
            "materials": [{
                "name": "HumanMaterial",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.85, 0.72, 0.62, 1.0],
                    "metallicFactor": 0.1,
                    "roughnessFactor": 0.6
                }
            }],
            "buffers": [{
                "byteLength": len(buffer_data),
                "uri": "data:application/octet-stream;base64," + b64_buffer
            }],
            "bufferViews": [
                {"buffer": 0, "byteOffset": pos_offset, "byteLength": len(pos_bytes), "target": 34962},
                {"buffer": 0, "byteOffset": norm_offset, "byteLength": len(norm_bytes), "target": 34962},
                {"buffer": 0, "byteOffset": uv_offset, "byteLength": len(uv_bytes), "target": 34962},
                {"buffer": 0, "byteOffset": idx_offset, "byteLength": len(idx_bytes), "target": 34963}
            ],
            "accessors": [
                {"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(positions)//3, "type": "VEC3", "max": max_pos, "min": min_pos},
                {"bufferView": 1, "byteOffset": 0, "componentType": 5126, "count": len(normals)//3, "type": "VEC3"},
                {"bufferView": 2, "byteOffset": 0, "componentType": 5126, "count": len(texcoords)//2, "type": "VEC2"},
                {"bufferView": 3, "byteOffset": 0, "componentType": idx_component_type, "count": len(indices), "type": "SCALAR"}
            ]
        }

        with open(filepath, "w") as f:
            json.dump(gltf, f, indent=2)


def build_human_model():
    mesh = Mesh()

    # Total human height = ~1.78 meters (178 units, 1 unit = 1 cm)
    # Ground at Y = 0. Head top at Y = ~178.

    # 1. HEAD & HAIR
    # Head skull center at (0, 163, 0), rx=9.5, ry=11.5, rz=10.5
    mesh.add_ellipsoid((0, 163, 0.5), rx=9.5, ry=11.5, rz=10.5, lat_bands=14, lon_bands=20, mat="skin")

    # Hair / Hair volume: top cap slightly larger
    mesh.add_ellipsoid((0, 167, -0.5), rx=10.0, ry=9.0, rz=11.0, lat_bands=12, lon_bands=20, mat="hair")

    # Jaw / Chin: taper down
    mesh.add_ellipsoid((0, 155, 3.0), rx=6.0, ry=4.5, rz=6.5, lat_bands=8, lon_bands=14, mat="skin")

    # Nose
    mesh.add_ellipsoid((0, 161.5, 11.2), rx=1.2, ry=2.4, rz=2.0, lat_bands=6, lon_bands=10, mat="skin")

    # Ears (Left and Right)
    mesh.add_ellipsoid((-9.6, 162.5, 0.0), rx=1.4, ry=3.2, rz=2.0, lat_bands=6, lon_bands=10, mat="skin")
    mesh.add_ellipsoid((9.6, 162.5, 0.0), rx=1.4, ry=3.2, rz=2.0, lat_bands=6, lon_bands=10, mat="skin")

    # Eyes / Brow Ridge
    mesh.add_ellipsoid((-3.5, 163.5, 9.6), rx=2.0, ry=1.4, rz=1.2, lat_bands=6, lon_bands=10, mat="hair")
    mesh.add_ellipsoid((3.5, 163.5, 9.6), rx=2.0, ry=1.4, rz=1.2, lat_bands=6, lon_bands=10, mat="hair")

    # 2. NECK
    mesh.add_capsule((0, 154, 0.5), (0, 144, 0.2), radius1=5.2, radius2=5.8, segments=14, rings=4, mat="skin")

    # 3. TORSO (Chest, Upper body, Waist, Pelvis)
    # Upper Chest / Deltoid base: Y=144 down to Y=126
    mesh.add_cylinder_segment((0, 128, 0), bottom_rx=17.5, bottom_rz=10.5,
                              top_center=(0, 144, 0), top_rx=19.5, top_rz=11.5,
                              segments=20, mat="clothes")

    # Pectoral bulk / Chest volume
    mesh.add_ellipsoid((-7.5, 134, 6.0), rx=6.5, ry=5.5, rz=5.0, lat_bands=8, lon_bands=14, mat="clothes")
    mesh.add_ellipsoid((7.5, 134, 6.0), rx=6.5, ry=5.5, rz=5.0, lat_bands=8, lon_bands=14, mat="clothes")

    # Abdomen / Waist: Y=128 down to Y=106
    mesh.add_cylinder_segment((0, 106, -0.5), bottom_rx=15.0, bottom_rz=10.0,
                              top_center=(0, 128, 0), top_rx=17.5, top_rz=10.5,
                              segments=20, mat="clothes")

    # Pelvis / Hips: Y=106 down to Y=90
    mesh.add_cylinder_segment((0, 90, -0.5), bottom_rx=16.5, bottom_rz=11.0,
                              top_center=(0, 106, -0.5), top_rx=15.0, top_rz=10.0,
                              segments=20, mat="pants")

    # Gluteal / Pelvis rounded base
    mesh.add_ellipsoid((-7.5, 92, -3.0), rx=7.0, ry=6.0, rz=6.5, lat_bands=8, lon_bands=14, mat="pants")
    mesh.add_ellipsoid((7.5, 92, -3.0), rx=7.0, ry=6.0, rz=6.5, lat_bands=8, lon_bands=14, mat="pants")

    # 4. SHOULDERS & ARMS (Left side: negative X, Right side: positive X)
    for sign in [-1, 1]:
        # Shoulder / Deltoid
        mesh.add_ellipsoid((sign * 20.0, 140.0, 0.0), rx=5.5, ry=6.0, rz=5.5, lat_bands=8, lon_bands=14, mat="clothes")

        # Upper Arm (Shoulder to Elbow)
        # Bicep/Tricep angle slightly flared outwards: Shoulder at 20.0, 139, 0 -> Elbow at 24.5, 112, -1.0
        p_shoulder = (sign * 20.0, 138.0, 0.0)
        p_elbow = (sign * 25.0, 112.0, -1.0)
        mesh.add_capsule(p_shoulder, p_elbow, radius1=4.8, radius2=4.0, segments=12, rings=5, mat="skin")

        # Elbow Joint
        mesh.add_ellipsoid(p_elbow, rx=3.8, ry=3.8, rz=3.8, lat_bands=6, lon_bands=12, mat="skin")

        # Forearm (Elbow to Wrist): Wrist at 28.0, 87, 2.0
        p_wrist = (sign * 28.0, 87.0, 2.0)
        mesh.add_capsule(p_elbow, p_wrist, radius1=3.9, radius2=3.0, segments=12, rings=5, mat="skin")

        # Hand / Palm: centered at wrist + down
        p_palm = (sign * 29.5, 80.0, 3.0)
        mesh.add_ellipsoid(p_palm, rx=3.2, ry=4.5, rz=1.8, lat_bands=6, lon_bands=12, mat="skin")

        # Thumb
        p_thumb_base = (sign * 27.5, 81.5, 4.0)
        p_thumb_tip = (sign * 26.5, 77.5, 5.0)
        mesh.add_capsule(p_thumb_base, p_thumb_tip, radius1=1.1, radius2=0.9, segments=6, rings=2, mat="skin")

        # Fingers (grouped realistic character hand)
        p_fingers_tip = (sign * 30.0, 72.5, 3.0)
        mesh.add_capsule(p_palm, p_fingers_tip, radius1=2.8, radius2=2.0, segments=8, rings=3, mat="skin")

    # 5. LEGS & FEET (Hip to Knee, Knee to Ankle, Foot)
    for sign in [-1, 1]:
        # Hip joint
        p_hip = (sign * 9.5, 88.0, 0.0)

        # Knee joint
        p_knee = (sign * 10.2, 49.0, 1.0)

        # Thigh / Quad (Hip to Knee)
        mesh.add_capsule(p_hip, p_knee, radius1=7.8, radius2=5.6, segments=14, rings=6, mat="pants")

        # Knee cap
        mesh.add_ellipsoid(p_knee, rx=5.2, ry=5.0, rz=5.0, lat_bands=7, lon_bands=12, mat="pants")

        # Lower Leg / Calf (Knee to Ankle)
        p_ankle = (sign * 10.5, 9.0, -1.0)
        mesh.add_capsule(p_knee, p_ankle, radius1=5.2, radius2=3.8, segments=14, rings=6, mat="skin")

        # Foot / Shoe
        # Heel at ankle, foot extends forward in Z
        p_heel = (sign * 10.5, 4.5, -3.0)
        p_toe = (sign * 10.5, 3.5, 12.0)
        mesh.add_capsule(p_heel, p_toe, radius1=4.2, radius2=3.5, segments=12, rings=5, mat="shoes")

        # Sole / Bottom support
        mesh.add_ellipsoid((sign * 10.5, 2.0, 4.0), rx=4.2, ry=2.0, rz=10.0, lat_bands=6, lon_bands=12, mat="shoes")

    return mesh

if __name__ == "__main__":
    out_dir = "/home/user/RealLife"
    mesh = build_human_model()
    print(f"Generated human mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

    # Write MTL
    mtl_path = os.path.join(out_dir, "human.mtl")
    with open(mtl_path, "w") as f:
        f.write("""# Materials for Human 3D Model
newmtl skin
Kd 0.90 0.74 0.64
Ka 0.20 0.15 0.12
Ks 0.15 0.15 0.15
Ns 20.0
d 1.0

newmtl hair
Kd 0.22 0.15 0.10
Ka 0.10 0.08 0.05
Ks 0.25 0.25 0.25
Ns 35.0
d 1.0

newmtl clothes
Kd 0.18 0.42 0.72
Ka 0.08 0.15 0.25
Ks 0.30 0.30 0.30
Ns 25.0
d 1.0

newmtl pants
Kd 0.15 0.18 0.25
Ka 0.05 0.07 0.10
Ks 0.20 0.20 0.20
Ns 15.0
d 1.0

newmtl shoes
Kd 0.85 0.85 0.88
Ka 0.20 0.20 0.20
Ks 0.40 0.40 0.40
Ns 50.0
d 1.0
""")
    print(f"Wrote {mtl_path}")

    # Write OBJ
    obj_path = os.path.join(out_dir, "human.obj")
    mesh.export_obj(obj_path, "human.mtl")
    print(f"Wrote {obj_path}")

    # Write GLTF
    gltf_path = os.path.join(out_dir, "human.gltf")
    mesh.export_gltf(gltf_path)
    print(f"Wrote {gltf_path}")
