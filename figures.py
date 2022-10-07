import mathlib as ml
from numpy import arccos, arctan2
from gl import V3
import math

OPAQUE = 0
REFLECTIVE = 1
TRANSPARENT = 2

WHITE = (1,1,1)

class DirectionalLight(object):
    def __init__(self, direction = V3(0,-1,0), intensity = 1, color = WHITE ):
        self.direction = direction / ml.norm(direction)
        self.intensity = intensity
        self.color = color

class AmbientLight(object):
    def __init__(self, strength = 0, color = WHITE):
        self.strength = strength
        self.color = color

    def getColor(self):
        return (self.strength * self.color[0],
                self.strength * self.color[1],
                self.strength * self.color[2])

class PointLight(object):
    # Luz con punto de origen que va en todas direcciones
    def __init__(self, position = V3(0,0,0), intensity = 1, color = WHITE):
        self.position = position
        self.intensity = intensity
        self.color = color

class Material(object):
    def __init__(self, diffuse = WHITE, spec = 1, ior = 1, texture = None, matType = OPAQUE):
        self.diffuse = diffuse
        self.spec = spec
        self.ior = ior
        self.texture = texture
        self.matType = matType


class Intersect(object):
    def __init__(self, distance, point, normal, texCoords, sceneObject):
        self.distance = distance
        self.point = point
        self.normal = normal
        self.texCoords = texCoords
        self.sceneObject = sceneObject

class Sphere(object):
    def __init__(self, center, radius, material = Material()):
        self.center = center
        self.radius = radius
        self.material = material

    def ray_intersect(self, orig, dir):

        L = ml.subtract(self.center, orig)
        l = ml.norm(L)

        tca = ml.dot(L, dir)

        d = (l**2 - tca**2)
        if d > self.radius ** 2:
            return None

        thc = (self.radius**2 - d) ** 0.5
        t0 = tca - thc
        t1 = tca + thc

        if t0 < 0:
            t0 = t1

        if t0 < 0:
            return None

        # P = O + t * D
        hit = ml.add(orig, t0 * dir )
        normal = ml.subtract( hit, self.center )
        normal = normal / ml.norm(normal) #la normalizo

        u = 1 - ((arctan2(normal[2], normal[0] ) / (2 * 3.14)) + 0.5)
        v = arccos(-normal[1]) / 3.14

        uvs = (u,v)

        return Intersect( distance = t0,
                          point = hit,
                          normal = normal,
                          texCoords = uvs,
                          sceneObject = self)


class Plane(object):
    def __init__(self, position, normal, material = Material()):
        self.position = position
        self.normal = normal / ml.norm(normal)
        self.material = material

    def ray_intersect(self, orig, dir):
        #t = (( planePos - origRayo) dot planeNormal) / (dirRayo dot planeNormal)
        denom = ml.dot(dir, self.normal)

        if abs(denom) > 0.0001:
            num = ml.dot(ml.subtract(self.position, orig), self.normal)
            t = num / denom
            if t > 0:
                # P = O + t * D
                hit = ml.add(orig, t * dir)

                return Intersect(distance = t,
                                 point = hit,
                                 normal = self.normal,
                                 texCoords = None,
                                 sceneObject = self)

        return None

class AABB(object):
    # Axis Aligned Bounding Box
    def __init__(self, position, size, material = Material()):
        self.position = position
        self.size = size
        self.material = material
        self.planes = []

        self.boundsMin = [0,0,0]
        self.boundsMax = [0,0,0]

        halfSizeX = size[0] / 2
        halfSizeY = size[1] / 2
        halfSizeZ = size[2] / 2

        #Sides
        self.planes.append(Plane( ml.add(position, V3(halfSizeX,0,0)), V3(1,0,0), material))
        self.planes.append(Plane( ml.add(position, V3(-halfSizeX,0,0)), V3(-1,0,0), material))

        # Up and down
        self.planes.append(Plane( ml.add(position, V3(0,halfSizeY,0)), V3(0,1,0), material))
        self.planes.append(Plane( ml.add(position, V3(0,-halfSizeY,0)), V3(0,-1,0), material))

        # Front and Back
        self.planes.append(Plane( ml.add(position, V3(0,0,halfSizeZ)), V3(0,0,1), material))
        self.planes.append(Plane( ml.add(position, V3(0,0,-halfSizeZ)), V3(0,0,-1), material))

        #Bounds
        epsilon = 0.001
        for i in range(3):
            self.boundsMin[i] = self.position[i] - (epsilon + self.size[i]/2)
            self.boundsMax[i] = self.position[i] + (epsilon + self.size[i]/2)


    def ray_intersect(self, orig, dir):
        intersect = None
        t = float('inf')

        uvs = None

        for plane in self.planes:
            planeInter = plane.ray_intersect(orig, dir)
            if planeInter is not None:
                # Si estoy dentro de los bounds
                if planeInter.point[0] >= self.boundsMin[0] and planeInter.point[0] <= self.boundsMax[0]:
                    if planeInter.point[1] >= self.boundsMin[1] and planeInter.point[1] <= self.boundsMax[1]:
                        if planeInter.point[2] >= self.boundsMin[2] and planeInter.point[2] <= self.boundsMax[2]:
                            #Si soy el plano mas cercano
                            if planeInter.distance < t:
                                t = planeInter.distance
                                intersect = planeInter

                                u, v = 0, 0

                                if abs(plane.normal[0]) > 0:
                                    # mapear uvs para eje X, uso coordenadas en Y y Z.
                                    u = (planeInter.point[1] - self.boundsMin[1]) / (self.boundsMax[1] - self.boundsMin[1])
                                    v = (planeInter.point[2] - self.boundsMin[2]) / (self.boundsMax[2] - self.boundsMin[2])

                                elif abs(plane.normal[1]) > 0:
                                    # mapear uvs para eje Y, uso coordenadas en X y Z.
                                    u = (planeInter.point[0] - self.boundsMin[0]) / (self.boundsMax[0] - self.boundsMin[0])
                                    v = (planeInter.point[2] - self.boundsMin[2]) / (self.boundsMax[2] - self.boundsMin[2])

                                elif abs(plane.normal[2]) > 0:
                                    # mapear uvs para eje Z, uso coordenadas en X y Y.
                                    u = (planeInter.point[0] - self.boundsMin[0]) / (self.boundsMax[0] - self.boundsMin[0])
                                    v = (planeInter.point[1] - self.boundsMin[1]) / (self.boundsMax[1] - self.boundsMin[1])

                                uvs = (u,v)


        if intersect is None:
            return None

        return Intersect(distance = intersect.distance,
                         point = intersect.point,
                         normal = intersect.normal,
                         texCoords = uvs,
                         sceneObject = self)

#Referencia: https://www.scratchapixel.com/lessons/3d-basic-rendering/ray-tracing-rendering-a-triangle/ray-triangle-intersection-geometric-solution
class Triangle(object):
    def __init__(self, v0, v1, v2, t, material):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.t = t
        self.material = material
    
    def ray_intersect(self, orig, dir):
        v0v1 = ml.subtract(self.v1, self.v0)
        v0v2 = ml.subtract(self.v2, self.v0)

        N = ml.cross(v0v1, v0v2)
        area2 = N.size

        eps = 1.0
        while eps + 1 > 1:
            eps /= 2
        eps *= 2

        NdotDireccionRayo = ml.dot(N, dir)
        if math.fabs(NdotDireccionRayo) < eps:
            return None
        
        d = -(ml.dot(N, self.v0))

        self.t = -(ml.dot(N, orig) + d) / NdotDireccionRayo

        if self.t < 0:
            return None

        P = orig+self.t*dir

        #Edge 0
        edge0 = ml.subtract(self.v1, self.v0)
        vp0 = ml.subtract(P, self.v0)
        
        C = ml.cross(edge0, vp0)

        if ml.dot(N, C) < 0:
            return None
        
        #Edge 1
        
        edge1 = ml.subtract(self.v2, self.v1)
        vp1 = ml.subtract(P, self.v1)
        C = ml.cross(edge1, vp1)

        if ml.dot(N, C) < 0:
            return None

        #Edge 2
        edge2 = ml.subtract(self.v0, self.v2)
        vp2 = ml.subtract(P, self.v2)
        C = ml.cross(edge2, vp2)

        if ml.dot(N,C) < 0:
            return None

        return Intersect(
            distance=self.t,
            point=P,
            normal=N,
            texcoords=None,
            sceneObj=self
        )
class Disk(object):
    def __init__(self, position, radius, normal,  material):
        self.plane = Plane(position, normal, material)
        self.material = material
        self.radius = radius

    def ray_intersect(self, orig, dir):

        intersect = self.plane.ray_intersect(orig, dir)

        if intersect is None:
            return None

        contact = ml.subtract(intersect.point, self.plane.position)
        contact = ml.norm(contact) 

        if contact > self.radius:
            return None

        return Intersect(distance = intersect.distance,
                         point = intersect.point,
                         normal = self.plane.normal,
                         texcoords = None,
                         sceneObj = self)