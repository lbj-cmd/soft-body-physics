# World_cython.pyx
# Cython implementation of the World class for faster physics calculations

import numpy as np
cimport numpy as np
from libc.math cimport sqrt

cdef class Vector:
    cdef public double x, y, z

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)

    def __imul__(self, scalar):
        self.x *= scalar
        self.y *= scalar
        self.z *= scalar
        return self

    def __div__(self, scalar):
        return Vector(self.x / scalar, self.y / scalar, self.z / scalar)

    def __idiv__(self, scalar):
        self.x /= scalar
        self.y /= scalar
        self.z /= scalar
        return self

    def length(self):
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalized(self):
        cdef double l = self.length()
        if l != 0.0:
            return Vector(self.x / l, self.y / l, self.z / l)
        return Vector(0.0, 0.0, 0.0)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z


from Material import Material

cdef class Particle:
    cdef public object material
    cdef public Vector position, previous, velocity, acceleration

    def __init__(self, x=0.0, y=0.0, z=0.0, material=None):
        self.position = Vector(x, y, z)
        self.previous = Vector(x, y, z)
        self.velocity = Vector(0.0, 0.0, 0.0)
        self.acceleration = Vector(0.0, 0.0, 0.0)
        if material is None:
            self.material = Material()
        else:
            self.material = material

    cdef void Simulate(self, double delta):
        if self.material.mass == 0.0:
            return
        # Verlet integration
        self.velocity.x = 2.0 * self.position.x - self.previous.x
        self.velocity.y = 2.0 * self.position.y - self.previous.y
        self.velocity.z = 2.0 * self.position.z - self.previous.z

        self.previous.x = self.position.x
        self.previous.y = self.position.y
        self.previous.z = self.position.z

        self.position.x = self.velocity.x + self.acceleration.x * delta**2.0
        self.position.y = self.velocity.y + self.acceleration.y * delta**2.0
        self.position.z = self.velocity.z + self.acceleration.z * delta**2.0

        self.velocity.x = self.position.x - self.previous.x
        self.velocity.y = self.position.y - self.previous.y
        self.velocity.z = self.position.z - self.previous.z

        self.acceleration.x = 0.0
        self.acceleration.y = 0.0
        self.acceleration.z = 0.0

    cdef void Accelerate(self, Vector rate):
        self.acceleration.x += rate.x
        self.acceleration.y += rate.y
        self.acceleration.z += rate.z

    cdef void ApplyImpulse(self, Vector impulse):
        if self.material.mass != 0.0:
            self.position.x += impulse.x / self.material.mass
            self.position.y += impulse.y / self.material.mass
            self.position.z += impulse.z / self.material.mass


cdef class Constraint:
    cdef public Particle node1, node2
    cdef public double target, stiff

    def __init__(self, Particle p1, Particle p2, double s, d=None):
        cdef double dx, dy, dz
        self.node1 = p1
        self.node2 = p2
        self.stiff = s
        if d is None:
            dx = p2.position.x - p1.position.x
            dy = p2.position.y - p1.position.y
            dz = p2.position.z - p1.position.z
            self.target = sqrt(dx*dx + dy*dy + dz*dz)
        else:
            self.target = d

    cdef void Relax(self):
        cdef double dx = self.node2.position.x - self.node1.position.x
        cdef double dy = self.node2.position.y - self.node1.position.y
        cdef double dz = self.node2.position.z - self.node1.position.z
        cdef double dist = sqrt(dx*dx + dy*dy + dz*dz)
        cdef double diff = 0.5 * self.stiff * (dist - self.target)
        cdef double inv_dist = 1.0 / dist if dist != 0.0 else 0.0

        cdef Vector F = Vector(dx * inv_dist * diff, dy * inv_dist * diff, dz * inv_dist * diff)

        if self.node1.material.mass != 0.0 and self.node2.material.mass == 0.0:
            self.node1.ApplyImpulse(F * 2.0)
        elif self.node1.material.mass == 0.0 and self.node2.material.mass != 0.0:
            self.node2.ApplyImpulse(F * -2.0)
        else:
            self.node1.ApplyImpulse(F)
            self.node2.ApplyImpulse(F * -1.0)


cdef class World:
    cdef public Vector size, hsize, gravity
    cdef public int step
    cdef public double delta
    cdef public list particles
    cdef public list constraints

    def __init__(self, size=None, gravity=None, t=8):
        if size is None:
            size = Vector(0.0, 0.0, 0.0)
        if gravity is None:
            gravity = Vector(0.0, 9.8, 0.0)
        self.size = size
        self.hsize = size * 0.5
        self.gravity = gravity
        if t < 1:
            self.step = 1
            self.delta = 1.0
        else:
            self.step = t
            self.delta = 1.0 / self.step
        self.particles = []
        self.constraints = []

    def Simulate(self):
        cdef int i, j
        cdef Particle p
        cdef Constraint c

        for i in range(self.step):
            # Accelerate particles
            for p in self.particles:
                p.Accelerate(self.gravity)

            # Simulate particle motion
            for p in self.particles:
                p.Simulate(self.delta)

            # Relax constraints
            for c in self.constraints:
                c.Relax()

    def AddParticle(self, x, y, z=0.0, material=None):
        cdef Particle p = Particle(x, y, z, material)
        self.particles.append(p)
        return p

    def AddConstraint(self, p1, p2, s, d=None):
        cdef Constraint c = Constraint(p1, p2, s, d)
        self.constraints.append(c)
        return c