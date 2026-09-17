#!/usr/bin/env python3
"""
Generate ULTRA high-poly realistic male body OBJ
20-30k faces, detailed anatomy
"""
import math

class ObjBuilder:
    def __init__(self):
        self.vertices = []
        self.normals = []
        self.uvs = []
        self.faces = []
        self.current_mat = "Skin"
        self.current_group = "Body"

    def add_vertex(self, x,y,z, nx,ny,nz, u=0,v=0):
        self.vertices.append((x,y,z))
        self.normals.append((nx,ny,nz))
        self.uvs.append((u,v))
        return len(self.vertices)

    def add_face(self, v1,v2,v3):
        self.faces.append((v1,v2,v3, self.current_mat, self.current_group))

    def set_material(self, name):
        self.current_mat = name
    def set_group(self, name):
        self.current_group = name

    def add_sphere(self, cx,cy,cz, radius, seg_u=32, seg_v=20, scale_x=1, scale_y=1, scale_z=1):
        start_idx = len(self.vertices) + 1
        for iv in range(seg_v+1):
            v = iv / seg_v
            phi = v * math.pi
            for iu in range(seg_u+1):
                u = iu / seg_u
                theta = u * 2*math.pi
                x = math.sin(phi)*math.cos(theta)
                y = math.cos(phi)
                z = math.sin(phi)*math.sin(theta)
                nx, ny, nz = x, y, z
                px = cx + x*radius*scale_x
                py = cy + y*radius*scale_y
                pz = cz + z*radius*scale_z
                self.add_vertex(px,py,pz, nx,ny,nz, u, v)
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

    def add_cylinder(self, cx,cy,cz, r_top, r_bottom, height, radial=36, height_seg=6, ex=1, ez=1, cap_top=True, cap_bottom=True):
        start_idx = len(self.vertices) + 1
        for ih in range(height_seg+1):
            y = cy - height/2 + (ih/height_seg)*height
            v = ih/height_seg
            r = r_bottom + (r_top - r_bottom)*(ih/height_seg)
            for ir in range(radial+1):
                u = ir/radial
                theta = u*2*math.pi
                x = math.cos(theta)*r*ex
                z = math.sin(theta)*r*ez
                nx = math.cos(theta)
                nz = math.sin(theta)
                self.add_vertex(cx+x, y, cz+z, nx, 0, nz, u, v)
        for ih in range(height_seg):
            for ir in range(radial):
                a = start_idx + ih*(radial+1) + ir
                b = start_idx + ih*(radial+1) + ir + 1
                c = start_idx + (ih+1)*(radial+1) + ir
                d = start_idx + (ih+1)*(radial+1) + ir + 1
                self.add_face(a, c, b)
                self.add_face(b, c, d)
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

    def add_capsule(self, cx,cy,cz, radius, height, radial=32, cap_seg=10):
        self.add_cylinder(cx,cy,cz, radius, radius, height, radial=radial, height_seg=4, cap_top=False, cap_bottom=False)
        self.add_sphere(cx, cy + height/2, cz, radius, seg_u=radial, seg_v=cap_seg, scale_y=0.9)
        self.add_sphere(cx, cy - height/2, cz, radius, seg_u=radial, seg_v=cap_seg, scale_y=0.9)

    def add_box(self, cx,cy,cz, sx,sy,sz):
        hx, hy, hz = sx/2, sy/2, sz/2
        pts = [(cx-hx,cy-hy,cz-hz),(cx+hx,cy-hy,cz-hz),(cx+hx,cy+hy,cz-hz),(cx-hx,cy+hy,cz-hz),
               (cx-hx,cy-hy,cz+hz),(cx+hx,cy-hy,cz+hz),(cx+hx,cy+hy,cz+hz),(cx-hx,cy+hy,cz+hz)]
        faces_idx = [(0,1,2,3),(5,4,7,6),(4,0,3,7),(1,5,6,2),(4,5,1,0),(3,2,6,7)]
        fn = [(0,0,-1),(0,0,1),(-1,0,0),(1,0,0),(0,-1,0),(0,1,0)]
        for fi,(i0,i1,i2,i3) in enumerate(faces_idx):
            nx,ny,nz = fn[fi]
            v0=self.add_vertex(*pts[i0],nx,ny,nz,0,0)
            v1=self.add_vertex(*pts[i1],nx,ny,nz,1,0)
            v2=self.add_vertex(*pts[i2],nx,ny,nz,1,1)
            v3=self.add_vertex(*pts[i3],nx,ny,nz,0,1)
            self.add_face(v0,v1,v2)
            self.add_face(v0,v2,v3)

    def save(self, obj_path, mtl_path):
        with open(obj_path,'w') as f:
            f.write(f"# Ultra Realistic Male Body - {len(self.vertices)} verts {len(self.faces)} faces\n")
            f.write(f"# Generated to match reference image 3d_model_man_underwear.jpg\n")
            f.write(f"mtllib {mtl_path.split('/')[-1]}\n")
            f.write("o MaleBody_Ultra\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for vt in self.uvs:
                f.write(f"vt {vt[0]:.6f} {vt[1]:.6f}\n")
            for vn in self.normals:
                f.write(f"vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n")
            cur_mat=None; cur_grp=None
            for v1,v2,v3,mat,grp in self.faces:
                if grp!=cur_grp:
                    f.write(f"g {grp}\n"); cur_grp=grp
                if mat!=cur_mat:
                    f.write(f"usemtl {mat}\n"); cur_mat=mat
                f.write(f"f {v1}/{v1}/{v1} {v2}/{v2}/{v2} {v3}/{v3}/{v3}\n")
        print(f"OBJ saved: {obj_path} - {len(self.vertices)} verts {len(self.faces)} faces")
        with open(mtl_path,'w') as f:
            f.write("""newmtl Skin
Ka 0.18 0.14 0.11
Kd 0.92 0.76 0.66
Ks 0.35 0.35 0.35
Ns 45.0
d 1.0
illum 2

newmtl SkinDark
Ka 0.14 0.10 0.08
Kd 0.80 0.62 0.54
Ks 0.25 0.25 0.25
Ns 35.0
illum 2

newmtl Underwear
Ka 0.02 0.02 0.02
Kd 0.07 0.07 0.08
Ks 0.20 0.20 0.22
Ns 25.0
d 1.0
illum 2

newmtl Hair
Ka 0.04 0.03 0.02
Kd 0.12 0.10 0.08
Ks 0.08 0.08 0.08
Ns 12.0
illum 2

newmtl Eye
Ka 0.01 0.01 0.01
Kd 0.15 0.15 0.15
Ks 0.8 0.8 0.8
Ns 100.0
illum 2
""")

def build():
    b=ObjBuilder()
    # HEAD - high poly
    b.set_group("Head"); b.set_material("Skin")
    b.add_sphere(0,1.85,0.02,0.138, seg_u=40, seg_v=24, scale_x=0.96, scale_y=1.18, scale_z=1.02)
    b.add_box(0,1.745,0.065,0.165,0.095,0.17)
    b.add_box(0,1.825,0.155,0.032,0.065,0.045)
    b.set_material("Hair")
    b.add_sphere(0,1.905,0.02,0.14, seg_u=32, seg_v=12, scale_x=1.0, scale_y=0.58, scale_z=1.0)
    b.set_material("Eye")
    b.add_sphere(-0.046,1.845,0.125,0.013, seg_u=16, seg_v=10)
    b.add_sphere(0.046,1.845,0.125,0.013, seg_u=16, seg_v=10)

    b.set_group("Neck"); b.set_material("Skin")
    b.add_cylinder(0,1.705,0,0.068,0.078,0.15, radial=36, height_seg=4)

    b.set_group("Chest"); b.set_material("Skin")
    b.add_cylinder(0,1.56,0.025,0.235,0.245,0.34, radial=40, height_seg=6, ex=1.28, ez=0.70)
    b.add_sphere(-0.125,1.57,0.15,0.135, seg_u=28, seg_v=16, scale_x=1.05, scale_y=0.65, scale_z=0.55)
    b.add_sphere(0.125,1.57,0.15,0.135, seg_u=28, seg_v=16, scale_x=1.05, scale_y=0.65, scale_z=0.55)
    b.add_sphere(-0.04,1.52,0.16,0.025, seg_u=12, seg_v=8)
    b.add_sphere(0.04,1.52,0.16,0.025, seg_u=12, seg_v=8)

    b.set_group("Abs")
    b.add_cylinder(0,1.31,0.015,0.205,0.195,0.30, radial=36, height_seg=6, ex=1.18, ez=0.64)
    for i in range(4):
        y=1.38 - i*0.09
        b.add_box(0,y,0.16,0.17,0.05,0.035)
    # obliques
    b.add_box(-0.15,1.22,0.05,0.06,0.18,0.06)
    b.add_box(0.15,1.22,0.05,0.06,0.18,0.06)

    b.set_group("Waist")
    b.add_cylinder(0,1.13,0,0.195,0.21,0.20, radial=36, height_seg=4, ex=1.12, ez=0.68)

    b.set_group("Shoulders")
    b.add_sphere(-0.325,1.53,0,0.088, seg_u=28, seg_v=18)
    b.add_sphere(0.325,1.53,0,0.088, seg_u=28, seg_v=18)
    b.add_cylinder(-0.325,1.53,0,0.085,0.085,0.08, radial=24, height_seg=2, ex=1, ez=1)
    b.add_cylinder(0.325,1.53,0,0.085,0.085,0.08, radial=24, height_seg=2, ex=1, ez=1)

    b.set_group("LeftArm")
    b.add_capsule(-0.44,1.33,0,0.075,0.36, radial=32, cap_seg=10)
    b.add_capsule(-0.52,0.99,0.025,0.062,0.34, radial=28, cap_seg=8)
    b.add_box(-0.56,0.73,0.025,0.085,0.15,0.055)
    for fx in [-0.022,0.022]:
        b.add_box(-0.56+fx,0.63,0.025,0.028,0.09,0.028)

    b.set_group("RightArm")
    b.add_capsule(0.44,1.33,0,0.075,0.36, radial=32, cap_seg=10)
    b.add_capsule(0.52,0.99,0.025,0.062,0.34, radial=28, cap_seg=8)
    b.add_box(0.56,0.73,0.025,0.085,0.15,0.055)
    for fx in [-0.022,0.022]:
        b.add_box(0.56+fx,0.63,0.025,0.028,0.09,0.028)

    b.set_group("Hips"); b.set_material("Underwear")
    b.add_cylinder(0,0.99,0,0.22,0.225,0.26, radial=48, height_seg=6, ex=1.18, ez=0.78)
    b.add_cylinder(-0.122,0.89,0.01,0.13,0.125,0.18, radial=28, height_seg=3)
    b.add_cylinder(0.122,0.89,0.01,0.13,0.125,0.18, radial=28, height_seg=3)

    b.set_group("LeftLeg"); b.set_material("Skin")
    b.add_capsule(-0.135,0.63,0,0.12,0.50, radial=36, cap_seg=10)
    b.add_sphere(-0.135,0.39,0.01,0.10, seg_u=24, seg_v=16)
    b.add_capsule(-0.135,0.19,0.01,0.095,0.44, radial=32, cap_seg=9)
    b.set_material("SkinDark")
    b.add_box(-0.135,0.035,0.09,0.13,0.075,0.28)

    b.set_group("RightLeg"); b.set_material("Skin")
    b.add_capsule(0.135,0.63,0,0.12,0.50, radial=36, cap_seg=10)
    b.add_sphere(0.135,0.39,0.01,0.10, seg_u=24, seg_v=16)
    b.add_capsule(0.135,0.19,0.01,0.095,0.44, radial=32, cap_seg=9)
    b.set_material("SkinDark")
    b.add_box(0.135,0.035,0.09,0.13,0.075,0.28)

    return b

if __name__=="__main__":
    b=build()
    b.save("/home/user/RealLife/male_model.obj", "/home/user/RealLife/male_model.mtl")
