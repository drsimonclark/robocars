# pyparticles - module for particle interactions in pygame

import math, random
from PIL import Image
from numpy import array, dot
from numpy.random import rand

Bounce = True

def addVectors(vector1,vector2):
	'''simple vector addition'''
	angle1 = vector1[0]
	length1 = vector1[1]
	angle2 = vector2[0]
	length2 = vector2[1]

	x = math.sin(angle1)*length1 + math.sin(angle2)*length2
	y = math.cos(angle1)*length1 + math.cos(angle2)*length2

	angle = 0.5*math.pi - math.atan2(y, x)
	length = math.hypot(x, y)

	return (angle, length)

def collide(p1, p2):
	'''if p1 and p2 have collided, resolve momentum'''

	dx = p1.x - p2.x
	dy = p1.y - p2.y

	dist = math.hypot(dx, dy)
	if dist < p1.size + p2.size:
		angle = math.atan2(dy, dx) + 0.5 * math.pi
		total_mass = p1.mass + p2.mass

		(p1.angle, p1.speed) = addVectors((p1.angle, p1.speed*(p1.mass-p2.mass)/total_mass), (angle, 2*p2.speed*p2.mass/total_mass))
		(p2.angle, p2.speed) = addVectors((p2.angle, p2.speed*(p2.mass-p1.mass)/total_mass), (angle+math.pi, 2*p1.speed*p1.mass/total_mass))
		elasticity = p1.elasticity * p2.elasticity
		p1.speed *= elasticity
		p2.speed *= elasticity

		overlap = 0.5*(p1.size + p2.size - dist+1)
		p1.x += math.sin(angle)*overlap
		p1.y -= math.cos(angle)*overlap
		p2.x -= math.sin(angle)*overlap
		p2.y += math.cos(angle)*overlap

def breed(p1,p2):
	'''given p1 and p2, produce an offspring with characteristics from both
	there is an equal chance of inheriting any characteristic'''

	coin = random.randint(0,1)
	if coin == 1:
		colour = p1.colour
	else:
		colour = p2.colour
	
	variation = 0.05
	
	control_rods = rand(p1.control_rods.shape[0],p1.control_rods.shape[1])
	for i in range(control_rods.shape[0]):
		
		for j in range(control_rods.shape[1]):
	
			coin = random.randint(0,1)

			if coin == 1:
				control_rods[i,j] = p1.control_rods[i,j] + random.uniform(-variation,variation)
			else:
				control_rods[i,j] = p2.control_rods[i,j] + random.uniform(-variation,variation)
	
	bias = rand(len(p1.bias))
	for i in range(len(bias)):
		coin = random.randint(0,1)
		if coin == 1:
			bias[i] = p1.bias[i] + random.uniform(-variation,variation)
		else:
			bias[i] = p2.bias[i] + random.uniform(-variation,variation)

	coin = random.randint(0,1)
	if coin == 1:
		fov = p1.fov + random.uniform(-5,5)
	else:
		fov = p2.fov + random.uniform(-5,5)
	
	return control_rods, bias, fov, colour

class Particle():
    def __init__(self, x, y, size, mass=1, **kargs):
        self.x = x
        self.y = y
        self.size = size
        self.mass = mass
        self.thickness = size
        self.speed = 0
        self.angle = math.pi/5
        self.elasticity = 0.5

        self.distance_front = 0
        self.distance_right = 0
        self.distance_left = 0

        # general attributes
        self.turning_angle = kargs.get('turning_angle', 0.1)
        self.acceleration = kargs.get('accn', 0.1)
        self.brake = -0.75*self.acceleration

        # controls on driving
        self.w = False	# activate acceleration
        self.a = False	# turn left
        self.s = False	# activate brake
        self.d = False	# turn right

        # unique attributes
        self.control_rods = kargs.get('control_rods', rand(5,4))
        self.bias = kargs.get('bias', rand(4))
        self.fov = kargs.get('fov', random.uniform(0, 90))
        self.colour = kargs.get('colour', (random.randint(0,255),random.randint(0,255),random.randint(0,255)))

        self.score = 0
        self.checkpoints_passed = 0
        self.fastest_lap = 999999
        self.stopwatch = 0 # time checkpoint 0 was last passed 
        self.wheel = 0

    def move(self):
        """ Update position based on speed, angle
            Update speed based on drag """
 		
        self.speed = self.speed*self.drag + self.acceleration*self.w + self.brake*self.s
        self.wheel = self.turning_angle*(self.d - self.a)
        self.angle += self.wheel
        
        #(self.angle, self.speed) = addVectors((self.angle, self.speed), gravity)
        self.x += math.sin(self.angle) * self.speed
        self.y -= math.cos(self.angle) * self.speed

    def control(self,env):
        '''Use inputs, control rods, and bias to determine if w, a, s, or d are pressed'''
        
        scaling = env.height/10
    
        inputs = [self.distance_left/scaling,self.distance_front/scaling,self.distance_right/scaling,self.speed,self.wheel]
        output = dot(inputs,self.control_rods) + self.bias

        threshold = 1
        if output[0] > threshold:
            self.w = True
        else:
            self.w = False

        if output[1] > threshold: 
            self.a = True
        else:
            self.a = False

        if output[2] > threshold: 
            self.s = True
        else:
            self.s = False

        if output[3] > threshold:
            self.d = True
        else:
            self.d = False
	
    def update_score(self,env):
        '''Update the score of the particle based on how quickly it has reached the checkpoints'''

        next_checkpoint = env.checkpoints[(self.checkpoints_passed+1) % len(env.checkpoints)]

        if math.hypot(self.x-next_checkpoint[0],self.y-next_checkpoint[1]) < 40:
        	
        	self.checkpoints_passed += 1
        	self.score += (1000*self.checkpoints_passed/env.time_elapsed + 1)**2

        if (self.checkpoints_passed+1) % len(env.checkpoints) == 1 and self.score > 0 and (env.time_elapsed - self.stopwatch) > 5000 :
       	       		
       		if (env.time_elapsed - self.stopwatch) < self.fastest_lap:
	       		
	       		self.fastest_lap = env.time_elapsed - self.stopwatch
	        	
	        	print('Fastest lap! ' + str(round(self.fastest_lap*100)/100000) + 's for particle ' + str(self.name))

       			self.stopwatch = env.time_elapsed

class Environment:
	
	def __init__(self, size, image, checkpoints, colliding):
		self.width = size[0]
		self.height = size[1]
		self.particles = []
		self.colour = (255,255,255)
		self.elasticity = 0.15
		self.track = array(Image.open(image))[:,:,1]/255
		self.track = self.track.astype(int)
		self.checkpoints = checkpoints
		self.colliding = colliding
		self.time_elapsed = 0
	
	def addParticles(self, n=1, **kargs):
		""" Add n particles with properties given by keyword arguments """
        
		for i in range(n):
			
			size = kargs.get('size', random.randint(10, 20))
			mass = size
			x = kargs.get('x', random.uniform(size, self.width - size))
			y = kargs.get('y', random.uniform(size, self.height - size))
			pos = (x,y)
			acceleration = kargs.get('accn',0.1)
			turning_angle = kargs.get('turning_angle',0.1)

			control_rods = kargs.get('control_rods', rand(5,4))
			bias = kargs.get('bias', rand(4))
			fov = kargs.get('fov', random.uniform(0, 90))
			colour = kargs.get('colour', (random.randint(0,255),random.randint(0,255),random.randint(0,255)))

			particle = Particle(x, y, size, mass, accn=acceleration, turning_angle=turning_angle, control_rods=control_rods, bias=bias, fov=fov, colour=colour)
			particle.speed = kargs.get('speed', random.random())
			particle.angle = math.pi/4
			particle.drag = 0.95
			particle.name = len(self.particles) + 1

			self.particles.append(particle)

	def update(self):
		'''Update the unique parameters of the particle'''
		
		for i, particle in enumerate(self.particles):
			particle.control(self)
			particle.move()
			self.bounce(particle)
			self.track_bounce(particle)
			if self.colliding:
				for particle2 in self.particles[i+1:]:
					collide(particle, particle2)
			self.distances(particle)
			particle.update_score(self)

	def bounce(self,particle):
		''' check if (x,y) is off the screen, bounce off limits'''

		if particle.x > self.width - particle.size:
			particle.x = 2*(self.width - particle.size) - particle.x
			particle.angle = - particle.angle
			particle.speed *= self.elasticity

		elif particle.x < particle.size:
			particle.x = 2*particle.size - particle.x
			particle.angle = - particle.angle
			particle.speed *= self.elasticity

		if particle.y > self.height - particle.size:
			particle.y = 2*(self.height - particle.size) - particle.y
			particle.angle = math.pi - particle.angle
			particle.speed *= self.elasticity

		elif particle.y < particle.size:
			particle.y = 2*particle.size - particle.y
			particle.angle = math.pi - particle.angle
			particle.speed *= self.elasticity

	def track_bounce(self,particle):
		'''check if the particle has hit a wall, approximately resolve momentum'''

		penalty = 0.25
		
		if self.track[int(particle.y), int(particle.x + particle.size)] == 0:
			particle.x -= particle.size/2
			particle.score -= penalty
			if Bounce:
				particle.speed *= self.elasticity
				particle.angle = - particle.angle
			else:
				article.speed *= -self.elasticity
				particle.angle = particle.angle
				
		if self.track[int(particle.y), int(particle.x - particle.size)] == 0:
			particle.x += particle.size/2
			particle.score -= penalty
			if Bounce:
				particle.angle = - particle.angle
				particle.speed *= self.elasticity
			else:
				article.speed *= -self.elasticity
				particle.angle = particle.angle

		if self.track[int(particle.y + particle.size), int(particle.x)] == 0:
			particle.y -= particle.size/2
			particle.score -= penalty
			if Bounce:
				particle.speed *= self.elasticity
				particle.angle = math.pi - particle.angle
			else: 
				particle.speed *= -self.elasticity
				particle.angle = particle.angle

		if self.track[int(particle.y - particle.size), int(particle.x)] == 0:
			particle.y += particle.size/2
			particle.score -= penalty
			if Bounce:
				particle.speed *= self.elasticity
				particle.angle = math.pi - particle.angle
			else: 
				particle.speed *= -self.elasticity
				particle.angle = particle.angle

	def distances(self,particle):
		''' Calculate distance from particle to container walls in front and to the side by "fov" degrees'''

		angle = math.pi - particle.angle
		fov = particle.fov*math.pi/180

		def calculation(self,particle,angle):
			
			test = False
			test_x = particle.x
			test_y = particle.y

			while test == False:
				
				test_x += 2*math.sin(angle)
				test_y += 2*math.cos(angle)

				if self.track[int(test_y),int(test_x)] == 0:
					test = True

			return test_x,test_y
    	
		test_x,test_y = calculation(self,particle,angle)
		particle.distance_front = math.hypot(test_x - particle.x, test_y - particle.y)	

		test_x,test_y = calculation(self,particle,angle-fov)
		particle.distance_right = math.hypot(test_x - particle.x, test_y - particle.y)		
		
		test_x,test_y = calculation(self,particle,angle+fov)
		particle.distance_left = math.hypot(test_x - particle.x, test_y - particle.y)