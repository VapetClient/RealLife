#!/usr/bin/env python3
"""
Generate ultra-realistic male body OBJ based on reference image
High-poly A-Pose, separate groups, PBR materials
"""
import math

class ObjBuilder:
    def __init__(self):
        self.vertices = []  # list of (x,y,z)
        self.normals = []   # list of (nx,ny,nz)
        self.uvs = []       # list of (u,v)
        self.faces = []     # list of (v1,v2,v3, mat_name, group)
        self.current_mat = "Skin"
        self.current_group = "Body"
        self.mat_groups = {}

    def add_vertex(self, x,y,z, nx,ny,nz, u=0,v=0):
        self.vertices.append((x,y,z))
        self.normals.append((nx,ny,nz))
        self.uvs.append((u,v))
        return len(self.vertices)  # 1-indexed

    def add_face(self, v1,v2,v3):
        self.faces.append((v1,v2,v3, self.current_mat, self.current_group))

    def set_material(self, name):
        self.current_mat = name

    def set_group(self, name):
        self.current_group = name

    def add_sphere(self, cx,cy,cz, radius, seg_u=24, seg_v=16, scale_x=1, scale_y=1, scale_z=1):
        """UV sphere"""
        start_idx = len(self.vertices) + 1
        verts = []
        # generate grid
        for iv in range(seg_v+1):
            v = iv / seg_v
            phi = v * math.pi
            for iu in range(seg_u+1):
                u = iu / seg_u
                theta = u * 2*math.pi
                x = math.sin(phi)*math.cos(theta)
                y = math.cos(phi)
                z = math.sin(phi)*math.sin(theta)
                # normal
                nx, ny, nz = x, y, z
                # position
                px = cx + x*radius*scale_x
                py = cy + y*radius*scale_y
                pz = cz + z*radius*scale_z
                # scale normal by scale (approx)
                # normalize normal accounting for scale
                n_len = math.sqrt((nx/scale_x)**2 + (ny/scale_y)**2 + (nz/scale_z)**2) if scale_x!=0 else 1
                # simplified: use original
                idx = self.add_vertex(px,py,pz, nx,ny,nz, u, v)
                verts.append(idx)
        # faces
        for iv in range(seg_v):
            for iu in range(seg_u):
                a = start_idx + iv*(seg_u+1) + iu
                b = start_idx + iv*(seg_u+1) + iu + 1
                c = start_idx + (iv+1)*(seg_u+1) + iu
                d = start_idx + (iv+1)*(seg_u+1) + iu + 1
                if iv != 0:
                    self.add_face(a, c, b)
                if iv != seg_v-1:
                    self.add_face(b, c, d)
        return verts

    def add_cylinder(self, cx,cy,cz, r_top, r_bottom, height, radial=24, height_seg=4, elliptical_x=1, elliptical_z=1, cap_top=True, cap_bottom=True):
        """Vertical cylinder centered at cx,cy,cz, height along Y"""
        start_idx = len(self.vertices) + 1
        # side vertices
        side_verts = []
        for ih in range(height_seg+1):
            y = cy - height/2 + (ih/height_seg)*height
            v = ih/height_seg
            # radius interpolation
            r = r_bottom + (r_top - r_bottom)*(ih/height_seg)
            for ir in range(radial+1):
                u = ir/radial
                theta = u*2*math.pi
                x = math.cos(theta)*r*elliptical_x
                z = math.sin(theta)*r*elliptical_z
                nx = math.cos(theta)
                nz = math.sin(theta)
                # normalize for ellipse
                n_len = math.sqrt((nx/elliptical_x)**2 + (nz/elliptical_z)**2) if elliptical_x!=0 else 1
                # keep simple
                px = cx + x
                pz = cz + z
                idx = self.add_vertex(px, y, pz, nx, 0, nz, u, v)
                side_verts.append(idx)
        # side faces
        for ih in range(height_seg):
            for ir in range(radial):
                a = start_idx + ih*(radial+1) + ir
                b = start_idx + ih*(radial+1) + ir + 1
                c = start_idx + (ih+1)*(radial+1) + ir
                d = start_idx + (ih+1)*(radial+1) + ir + 1
                self.add_face(a, c, b)
                self.add_face(b, c, d)
        # caps
        if cap_top:
            top_center = self.add_vertex(cx, cy+height/2, cz, 0,1,0, 0.5,0.5)
            top_start = start_idx + height_seg*(radial+1)
            for ir in range(radial):
                a = top_start + ir
                b = top_start + ir + 1
                self.add_face(a, b, top_center)
        if cap_bottom:
            bot_center = self.add_vertex(cx, cy-height/2, cz, 0,-1,0, 0.5,0.5)
            bot_start = start_idx
            for ir in range(radial):
                a = bot_start + ir
                b = bot_start + ir + 1
                self.add_face(b, a, bot_center)
        return side_verts

    def add_capsule(self, cx,cy,cz, radius, height, radial=20, cap_seg=8):
        """Capsule vertical"""
        # cylinder part
        cyl_h = height
        self.add_cylinder(cx,cy,cz, radius, radius, cyl_h, radial=radial, height_seg=2, cap_top=False, cap_bottom=False)
        # top hemisphere
        self.add_sphere(cx, cy + cyl_h/2, cz, radius, seg_u=radial, seg_v=cap_seg, scale_x=1, scale_y=0.8, scale_z=1)
        # bottom hemisphere
        self.add_sphere(cx, cy - cyl_h/2, cz, radius, seg_u=radial, seg_v=cap_seg, scale_x=1, scale_y=0.8, scale_z=1)

    def add_box(self, cx,cy,cz, sx,sy,sz):
        # 8 vertices
        hx, hy, hz = sx/2, sy/2, sz/2
        pts = [
            (cx-hx, cy-hy, cz-hz),
            (cx+hx, cy-hy, cz-hz),
            (cx+hx, cy+hy, cz-hz),
            (cx-hx, cy+hy, cz-hz),
            (cx-hx, cy-hy, cz+hz),
            (cx+hx, cy-hy, cz+hz),
            (cx+hx, cy+hy, cz+hz),
            (cx-hx, cy+hy, cz+hz),
        ]
        normals = [
            (0,0,-1),(0,0,-1),
            (0,0,1),(0,0,1),
            (-1,0,0),(1,0,0),
            (0,-1,0),(0,1,0)
        ]
        # create 6 faces *2 tris
        # We'll create 8 vertices per face for proper normals, simpler: duplicate
        faces_idx = [
            (0,1,2,3), # front -z
            (5,4,7,6), # back +z
            (4,0,3,7), # left -x
            (1,5,6,2), # right +x
            (4,5,1,0), # bottom -y
            (3,2,6,7), # top +y
        ]
        face_normals = [(0,0,-1),(0,0,1),(-1,0,0),(1,0,0),(0,-1,0),(0,1,0)]
        for fi, (i0,i1,i2,i3) in enumerate(faces_idx):
            nx,ny,nz = face_normals[fi]
            v0 = self.add_vertex(*pts[i0], nx,ny,nz, 0,0)
            v1 = self.add_vertex(*pts[i1], nx,ny,nz, 1,0)
            v2 = self.add_vertex(*pts[i2], nx,ny,nz, 1,1)
            v3 = self.add_vertex(*pts[i3], nx,ny,nz, 0,1)
            self.add_face(v0,v1,v2)
            self.add_face(v0,v2,v3)

    def save(self, obj_path, mtl_path):
        with open(obj_path, 'w') as f:
            f.write(f"# Realistic Male Body - Generated\n")
            f.write(f"# Vertices: {len(self.vertices)}\n")
            f.write(f"# Faces: {len(self.faces)}\n")
            f.write(f"mtllib {mtl_path.split('/')[-1]}\n")
            f.write(f"o MaleBody\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for vt in self.uvs:
                f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
            for vn in self.normals:
                f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")
            # group by material and group
            current_mat = None
            current_grp = None
            for (v1,v2,v3, mat, grp) in self.faces:
                if grp != current_grp:
                    f.write(f"g {grp}\n")
                    current_grp = grp
                if mat != current_mat:
                    f.write(f"usemtl {mat}\n")
                    current_mat = mat
                # f v/vt/vn
                f.write(f"f {v1}/{v1}/{v1} {v2}/{v2}/{v2} {v3}/{v3}/{v3}\n")
        print(f"Saved OBJ: {obj_path} - {len(self.vertices)} verts, {len(self.faces)} faces")
        # write MTL
        with open(mtl_path, 'w') as f:
            f.write("# Materials for realistic male body\n")
            f.write("newmtl Skin\n")
            f.write("Ka 0.15 0.12 0.10\n")
            f.write("Kd 0.91 0.75 0.65\n")
            f.write("Ks 0.25 0.25 0.25\n")
            f.write("Ns 32.0\n")
            f.write("d 1.0\n")
            f.write("illum 2\n\n")
            f.write("newmtl SkinDark\n")
            f.write("Ka 0.12 0.09 0.07\n")
            f.write("Kd 0.78 0.60 0.52\n")
            f.write("Ks 0.2 0.2 0.2\n")
            f.write("Ns 28.0\n")
            f.write("illum 2\n\n")
            f.write("newmtl Underwear\n")
            f.write("Ka 0.02 0.02 0.02\n")
            f.write("Kd 0.08 0.08 0.09\n")
            f.write("Ks 0.15 0.15 0.15\n")
            f.write("Ns 15.0\n")
            f.write("d 1.0\n")
            f.write("illum 2\n\n")
            f.write("newmtl Hair\n")
            f.write("Ka 0.05 0.04 0.03\n")
            f.write("Kd 0.15 0.13 0.11\n")
            f.write("Ks 0.1 0.1 0.1\n")
            f.write("Ns 10.0\n")
            f.write("illum 2\n")
        print(f"Saved MTL: {mtl_path}")

def build_body():
    b = ObjBuilder()
    # --- HEAD ---
    b.set_group("Head")
    b.set_material("Skin")
    b.add_sphere(0, 1.84, 0.02, 0.135, seg_u=28, seg_v=18, scale_x=0.95, scale_y=1.15, scale_z=1.0)
    # jaw
    b.add_box(0, 1.74, 0.06, 0.16, 0.09, 0.16)
    # nose subtle
    b.add_box(0, 1.82, 0.15, 0.03, 0.06, 0.04)
    # hair buzz
    b.set_material("Hair")
    b.add_sphere(0, 1.90, 0.02, 0.137, seg_u=24, seg_v=10, scale_x=1.0, scale_y=0.55, scale_z=1.0)
    # eyes
    b.set_material("SkinDark")
    b.add_sphere(-0.045, 1.84, 0.12, 0.012, seg_u=12, seg_v=8)
    b.add_sphere(0.045, 1.84, 0.12, 0.012, seg_u=12, seg_v=8)

    # --- NECK ---
    b.set_group("Neck")
    b.set_material("Skin")
    b.add_cylinder(0, 1.70, 0, 0.065, 0.075, 0.14, radial=24, height_seg=3, elliptical_x=1.0, elliptical_z=1.0)

    # --- TORSO ---
    # Chest - broad
    b.set_group("Chest")
    b.add_cylinder(0, 1.55, 0.02, 0.23, 0.24, 0.32, radial=28, height_seg=4, elliptical_x=1.25, elliptical_z=0.68)
    # Pectorals - two bulges
    b.add_sphere(-0.12, 1.56, 0.14, 0.13, seg_u=20, seg_v=12, scale_x=1.0, scale_y=0.6, scale_z=0.5)
    b.add_sphere(0.12, 1.56, 0.14, 0.13, seg_u=20, seg_v=12, scale_x=1.0, scale_y=0.6, scale_z=0.5)

    # Abs
    b.set_group("Abs")
    b.add_cylinder(0, 1.30, 0.01, 0.20, 0.19, 0.28, radial=26, height_seg=5, elliptical_x=1.15, elliptical_z=0.62)
    # 6-pack cubes subtle
    for i in range(3):
        y = 1.35 - i*0.11
        b.add_box(0, y, 0.15, 0.16, 0.06, 0.03)

    # Lower waist
    b.set_group("Waist")
    b.add_cylinder(0, 1.12, 0, 0.19, 0.205, 0.18, radial=26, height_seg=3, elliptical_x=1.1, elliptical_z=0.65)

    # --- SHOULDERS ---
    b.set_group("Shoulders")
    b.add_sphere(-0.32, 1.52, 0, 0.085, seg_u=20, seg_v=14)
    b.add_sphere(0.32, 1.52, 0, 0.085, seg_u=20, seg_v=14)

    # --- ARMS ---
    # Left upper
    b.set_group("LeftArm")
    # angled slightly out - we simulate by offset
    b.add_capsule(-0.43, 1.32, 0, 0.072, 0.34, radial=20, cap_seg=8)
    # Left lower
    b.add_capsule(-0.51, 0.98, 0.02, 0.058, 0.32, radial=18, cap_seg=6)
    # Left hand
    b.add_box(-0.55, 0.72, 0.02, 0.08, 0.14, 0.05)
    # fingers simplified
    for fx in [-0.02, 0.02]:
        b.add_box(-0.55+fx, 0.62, 0.02, 0.025, 0.08, 0.025)

    # Right upper
    b.set_group("RightArm")
    b.add_capsule(0.43, 1.32, 0, 0.072, 0.34, radial=20, cap_seg=8)
    b.add_capsule(0.51, 0.98, 0.02, 0.058, 0.32, radial=18, cap_seg=6)
    b.add_box(0.55, 0.72, 0.02, 0.08, 0.14, 0.05)
    for fx in [-0.02, 0.02]:
        b.add_box(0.55+fx, 0.62, 0.02, 0.025, 0.08, 0.025)

    # --- UNDERWEAR / HIPS ---
    b.set_group("Hips")
    b.set_material("Underwear")
    b.add_cylinder(0, 0.98, 0, 0.215, 0.22, 0.24, radial=32, height_seg=4, elliptical_x=1.15, elliptical_z=0.75)
    # underwear legs - two short cylinders
    b.add_cylinder(-0.12, 0.88, 0, 0.125, 0.12, 0.16, radial=20, height_seg=2, elliptical_x=1.0, elliptical_z=1.0)
    b.add_cylinder(0.12, 0.88, 0, 0.125, 0.12, 0.16, radial=20, height_seg=2, elliptical_x=1.0, elliptical_z=1.0)

    # --- LEGS ---
    b.set_group("LeftLeg")
    b.set_material("Skin")
    b.add_capsule(-0.13, 0.62, 0, 0.115, 0.48, radial=22, cap_seg=8)
    b.add_sphere(-0.13, 0.38, 0, 0.095, seg_u=18, seg_v=12) # knee
    b.add_capsule(-0.13, 0.18, 0, 0.09, 0.42, radial=20, cap_seg=7)
    # foot
    b.set_material("SkinDark")
    b.add_box(-0.13, 0.03, 0.08, 0.12, 0.07, 0.26)

    b.set_group("RightLeg")
    b.set_material("Skin")
    b.add_capsule(0.13, 0.62, 0, 0.115, 0.48, radial=22, cap_seg=8)
    b.add_sphere(0.13, 0.38, 0, 0.095, seg_u=18, seg_v=12)
    b.add_capsule(0.13, 0.18, 0, 0.09, 0.42, radial=20, cap_seg=7)
    b.set_material("SkinDark")
    b.add_box(0.13, 0.03, 0.08, 0.12, 0.07, 0.26)

    return b

if __name__ == "__main__":
    builder = build_body()
    builder.save("/home/user/RealLife/male_model.obj", "/home/user/RealLife/male_model.mtl")
