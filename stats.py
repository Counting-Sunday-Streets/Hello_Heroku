import scipy.integrate

def integrate_simps(points):
	"""
	Takes a list of tuples and integrates over them
	"""
	y_val = [tup[1] for tup in points]
	x_val = [tup[0] for tup in points]

	return scipy.integrate.trapz(y_val, x_val, 'avg')

print integrate_simps([(0, 0), (3, 3)])