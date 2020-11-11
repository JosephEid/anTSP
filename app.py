from flask import Flask
from flask import request
from flask import render_template
from flask import send_file, jsonify, json
from flask_socketio import SocketIO, emit
from threading import Lock

import io
import random
from flask import Response, redirect, url_for
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import itertools
import time
import sys
from math import sqrt
from colony import Colony
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
dir = os.path.dirname(os.path.realpath(__file__))
INSTANCES = [x for x in os.listdir(dir+'/instances/')]
async_mode = "eventlet"

socketio = SocketIO(app, async_mode=async_mode, debug=True)

thread = None
thread_lock = Lock()

class Node(object):
    """
    Node class representing cities within the instance
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, node):
        return sqrt((self.x - node.x) ** 2 + (self.y - node.y) ** 2)


class Instance(object):
    """
    Instance class representing the TSP Instance
    """
    def __init__(self, nodes, alpha, beta, decay, q):

        # Make a list of nodes as variables which are JSONifiable
        nodes_var = []
        for node in nodes:
            nodes_var.append(vars(node))
        self.nodes = nodes_var

        self.alpha = alpha
        self.beta = beta
        self.decay = decay
        self.q = q
        self.min_pheromone = 0.01
        self.local_deposit = 0.1

        self.distances = []
        self.pheromones = []
        colony = Colony()
        self.ants = colony.ants
        self.shortest_path = colony.shortest_path
        self.min_distance = colony.min_distance

        # Initialise the distances between nodes and pheromone trails
        for i in range(len(nodes)):
            distances = []
            pheromones = []
            for j in range(len(nodes)):
                distances.append(0 if i == j else nodes[i].distance(nodes[j]))
                pheromones.append(self.min_pheromone)
            self.distances.append(distances)
            self.pheromones.append(pheromones)

    def get_path_distance(self, path):
        """
        Returns the total total distance of a path taken
        """
        length = len(path)
        distance = 0
        for i in range(length):
            distance += self.distances[path[i]][path[(i + 1) % length]]
        return distance

    def update_pheromones(self, colony):
        """
        Updates pheromones between nodes globally, a way of letting ants know on future
        generations about the strongest paths to take.
        """

        # Decay all pheromone trails
        for i in range(len(self.nodes)):
            for j in range(len(self.nodes)):
                self.pheromones[i][j] *=(1- self.decay)

        # Add to edge pheromones if edge was part of successful tour
        for ant in colony.ants:
            distance = self.get_path_distance(ant.path)
            if distance <= colony.min_distance:
                for i, j in ant.nodes_traversed():
                    self.pheromones[i][j] += self.q / distance

        # Keep pheromone trails greater than or equal to 0.01, so nodes do not become
        # completely unviable choices.
        for i in range(len(self.nodes)):
            for j in range(len(self.nodes)):
                self.pheromones[i][j] = max(self.pheromones[i][j], self.min_pheromone)



    def aco(self, gens, current_gen, client):
        """
        Returns the generation reached and the shortest path found by the aco
        algorithm along with its distance
        """
        # The time at the start of the algorithm
        time_start = time.time()

        # Initalise the colony and its parameters
        self.colony = Colony()
        self.colony.ants = self.ants
        self.colony.shortest_path = self.shortest_path
        self.colony.min_distance = self.min_distance

        # Initialise an array to be append with nodes
        shortest_path = []

        # Do generations from the current generation to the generation number needed
        for i in range(current_gen, gens):

            # The current time
            time_now = time.time()
            time_elapsed = time_now-time_start
            # If exectutiion time has reached 25 seconds, return result
            if (time_elapsed) > 25:
                break

            # Ants within colony perform their tours
            self.colony.perform_tours(self)

            # Get the shortest tour found by the ants
            shortest_path = self.colony.shortest_path

            # Global update of pheromones
            self.update_pheromones(self.colony)

            # Generation successful, thus increase the generation reached
            gen_reached = i+1

            # Update Instance parameters to be returned to client
            self.shortest_path = shortest_path
            self.min_distance = self.colony.min_distance
            msg = "Generation " + str(i) + " distance " + str(round(self.colony.min_distance, 3)) + " path " + str(shortest_path)

            # Emit a message using SocketIO for a dynamic console
            socketio.emit('my event', msg, room=client)
            socketio.sleep(0.00000000001)

        return gen_reached, shortest_path, self.colony.min_distance


@app.route('/createcustom.png')
def create_custom():
    """
    Initialises a custom instance and returns it to the client in JSON form
    """
    # Extract initialisation parameters
    alpha = request.args.get('alpha')
    alpha = float(alpha)
    generations = request.args.get('generations')
    generations = int(generations)
    beta = request.args.get('beta')
    beta = float(beta)
    pec = request.args.get('pec')
    pec = float(pec)
    q = request.args.get('q')
    q = float(q)

    # Extract the custom coordinates and create a list of nodes
    coords = request.args.get('custom_coords')
    coords = str(coords)
    nodes = custom_nodes(coords)

    # Initialise instance
    i = Instance(nodes, alpha, beta, pec, q)

    return jsonify(nodes=i.nodes, alpha=i.alpha, beta=i.beta, decay=i.decay,
                   min_pheromone=i.min_pheromone, q=i.q,
                   local_deposit=i.local_deposit, distances=i.distances,
                   pheromones=i.pheromones, ants=i.ants, shortest_path=i.shortest_path,
                   min_distance=i.min_distance, message="Instance Initialised")

def custom_nodes(coords):
    """
    Creates a list of nodes given custom coordinates
    """
    coords = coords.split(':')
    coords.pop(len(coords)-1)
    nodes = []
    for i in coords:
        i = i.strip("()")
        vals = i.split(",")
        x = float(vals[0])
        y = float(vals[1])
        nodes.append(Node(x,y))

    return nodes

@app.route('/custompreview.png')
def custom_preview_png():
    """
    Creates a preview graph for a custom instance
    """
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    coords = request.args.get('custom_coords')
    coords = str(coords)
    coords = coords.split(':')
    coords.pop(len(coords)-1)
    for i in coords:
        i = i.strip("()")
        vals = i.split(",")
        x = float(vals[0])
        y = float(vals[1])
        axis.text(x,y, str(i))
        axis.scatter(x, y, c = 'b', label = str(i))

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/plotoptimum.png')
def plot_optimum_png():
    """
    Creates the optimal solution graph for the user to see
    """
    name = request.args.get('prev_instance')
    name = str(name)
    client = request.args.get('client')
    # Check that the optimal file path is found
    file_name = os.path.splitext(name)[0]
    optimal_found = os.path.isfile(dir+'/optimals/'+str(file_name)+'.opt.tour')
    # If found, create the graph, else return an empty graph
    if optimal_found:
        fig = create_optimal(name, client)
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')
    else:
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)
        axis.set_title(file_name + ' optimal path could not be found')
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')

def create_optimal(name, client):
    """
    Extracts the path and nodes from an optimal instance and plots it as a figure
    """
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    file_name = os.path.splitext(name)[0]
    ext = os.path.splitext(name)[1]
    dir = os.path.dirname(os.path.realpath(__file__))
    optimal_file = open(dir+'/optimals/'+file_name+'.opt.tour')

    file = open(dir+'/instances/'+file_name+ext)
    optimal_file.readline()
    optimal_file.readline()
    optimal_file.readline()
    optimal_file.readline()
    optimal_file.readline()
    optimal_path = optimal_file.readline()
    optimal_path = optimal_path.split()
    optimal_path = [int(n) - 1 for n in optimal_path]
    nodes = [] #Array storing nodes

    if (ext == ".tsp"):

        file.readline()
        file.readline()
        file.readline()
        no_nodes = int(file.readline().strip().split()[1])
        file.readline()
        file.readline()
        file.readline()

        for i in range(0, no_nodes):

            coords = file.readline().strip().split()[1:]
            x = float(coords[0])
            y = float(coords[1])
            axis.text(x,y, str(i))
            axis.scatter(x, y, c = 'b', label = str(i))
            nodes.append(Node(x,y))
    else:
        for nodeNo,line in enumerate(file): #enumerate used to obtain line numbers and thus node numbers
            coords = line.rsplit()[0].split(",")
            x = int(coords[0])
            y = int(coords[1])
            axis.scatter(x, y, c = 'b', label = nodeNo)
            axis.text(x+5,y+5, str(nodeNo))
            nodes.append(Node(x,y))

    # Initialise an Instance class to obtain the distance of the
    i = Instance(nodes, None, None, None, None)
    distance = i.get_path_distance(optimal_path)
    # Emit the distance of the optimal solution to the client
    socketio.emit('opt dist', round(distance, 3), room=client)
    socketio.sleep(0)
    axis.set_title(file_name + ' optimal path, Distance: ' + str(round(distance, 3)) + "\n"+ str(optimal_path))
    for i in range(len(optimal_path) - 1):
        start_node = nodes[optimal_path[i]]
        x1, y1 = start_node.x, start_node.y
        end_node = nodes[optimal_path[i+1]]
        x2, y2 = end_node.x, end_node.y
        axis.plot([x1,x2], [y1, y2])

    last_node = nodes[optimal_path[len(optimal_path)-1]]
    x1, y1 = last_node.x, last_node.y
    begin_node = nodes[optimal_path[0]]
    x2, y2 = begin_node.x, begin_node.y
    axis.scatter(x1, y1, c = 'b', label = str(optimal_path[len(optimal_path)-1]))
    axis.plot([x1,x2], [y1, y2])
    return fig

@app.route('/plotpreview.png')
def plot_preview_png():
    """
    Returns the instance preview as an image
    """
    name = request.args.get('prev_instance')
    name = str(name)
    fig = create_preview(name)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_preview(name):
    """
    Creates the instance preview figure
    """
    file_type = os.path.splitext(name)[1]

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    dir = os.path.dirname(os.path.realpath(__file__))
    file = open(dir+'/instances/'+name)
    if file_type == '.csv':

        for nodeNo,line in enumerate(file): #enumerate used to obtain line numbers and thus node numbers
            coords = line.rsplit()[0].split(",")

            x = int(coords[0])
            y = int(coords[1])
            axis.scatter(x, y, c = 'b', label = nodeNo)
            axis.set_title(name)
            axis.text(x+5,y+5, str(nodeNo))
    else:
        file.readline()
        file.readline()
        file.readline()
        no_nodes = int(file.readline().strip().split()[1])
        file.readline()
        file.readline()
        file.readline()

        for i in range(0, no_nodes):

            coords = file.readline().strip().split()[1:]
            x = float(coords[0])
            y = float(coords[1])
            axis.scatter(x, y, c = 'b', label = i)
            axis.set_title(name)
            axis.text(x,y, str(i))

    return fig

@app.route('/createinstance', methods=['GET'])
def create_graph():
    """
    Returns an Instance in JSON form
    """
    alpha = request.args.get('alpha')
    alpha = float(alpha)
    beta = request.args.get('beta')
    beta = float(beta)
    pec = request.args.get('pec')
    pec = float(pec)
    q = request.args.get('q')
    q = float(q)
    name = request.args.get('instance')
    name = str(name)

    nodes = create_nodes(name)
    i = Instance(nodes, alpha, beta, pec, q)

    return jsonify(nodes=i.nodes, alpha=i.alpha, beta=i.beta, decay=i.decay,
                   min_pheromone=i.min_pheromone, q=i.q,
                   local_deposit=i.local_deposit, distances=i.distances,
                   pheromones=i.pheromones, ants=i.ants, shortest_path=i.shortest_path,
                   min_distance=i.min_distance, message="Instance Initialised")

@app.route('/dogen', methods=['GET','POST'])
def do_generations():
    """
    Performs the aco algorithm on an TSP Instance
    """
    # Extract the data from the initialised Instance
    gens = request.args.get('gens')
    gens = int(gens)
    current_gen = request.args.get('currentGen')
    current_gen = int(current_gen)
    client = request.args.get('client')
    graph_data = request.get_json()
    nodes = graph_data['nodes']
    alpha = graph_data['alpha']
    beta = graph_data['beta']
    decay = graph_data['decay']
    min_pheromone = graph_data['min_pheromone']
    q = graph_data['q']
    local_deposit = graph_data['local_deposit']
    distances = graph_data['distances']
    pheromones = graph_data['pheromones']
    ants = graph_data['ants']
    shortest_path = graph_data['shortest_path']
    min_distance = graph_data['min_distance']
    # Initialise an Instance copy
    i = Instance([], float(alpha), float(beta), float(decay), float(q))
    # Alter the Instance copy with the Instance data
    i.nodes = nodes
    i.min_pheromone = min_pheromone
    i.q = q
    i.local_deposit = local_deposit
    i.distances = distances
    i.pheromones = pheromones
    i.ants = ants
    i.shortest_path = shortest_path
    i.min_distance = min_distance
    # Perform the aco algorithm on the instance
    gen_reached, path, distance = i.aco(gens, current_gen, client)

    # Create a message for the console to output
    msg = "Generation " + str(gen_reached) + " distance " + str(distance) + " path " + str(path)
    return jsonify(nodes=i.nodes, alpha=i.alpha, beta=i.beta, decay=i.decay,
                   min_pheromone=i.min_pheromone, q=i.q,
                   local_deposit=i.local_deposit, distances=i.distances,
                   pheromones=i.pheromones, ants=i.ants, shortest_path=i.shortest_path,
                   min_distance=round(i.min_distance, 3), gen_reached = gen_reached, message=msg)

@socketio.on('connect')
def test_connect():
    """
    SocketIO connectiong returns the client ID
    """
    s_id = request.sid
    s_id = str(s_id)
    print('anTSP initialised, client connected')
    emit('my response', s_id)

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@app.route('/plotGraph.png')
def plot_graph():
    """
    Plot the final solution
    """
    name = request.args.get('instance')
    name = str(name)
    distance = request.args.get('distance')
    path = request.args.get('path')
    if name == 'Custom':
        coords = request.args.get('coords')
        coords = str(coords)
        nodes = custom_nodes(coords)
    else:
        nodes = create_nodes(name)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    axis.set_title(name + " - Distance: "+ str(distance))
    path = str(path).split(',')
    path = [int(i) for i in path]
    for i in range(len(path) - 1):

        start_node = nodes[path[i]]
        x1, y1 = start_node.x, start_node.y
        axis.scatter(x1, y1, c = 'b', label = str(path[i]))
        axis.text(x1,y1, str(path[i]))
        end_node = nodes[path[i+1]]
        x2, y2 = end_node.x, end_node.y
        axis.plot([x1,x2], [y1, y2])

    last_node = nodes[path[len(path)-1]]
    x1, y1 = last_node.x, last_node.y
    axis.text(x1,y1, str(path[len(path)-1]))

    begin_node = nodes[path[0]]
    x2, y2 = begin_node.x, begin_node.y
    axis.scatter(x1, y1, c = 'b', label = str(path[len(path)-1]))
    axis.plot([x1,x2], [y1, y2])

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")

def create_nodes(name):
    """
    Creates a list of nodes for a standard non-custom TSP Instance
    """
    # Find the tsp instance file and extract its extension
    dir = os.path.dirname(os.path.realpath(__file__))
    file = open(dir+'/instances/'+name)
    ext = name.split('.')[1]
    nodes = [] #Array storing nodes

    # If .csv then just read nodes line by line
    if (ext == "csv"):
        for nodeNo,line in enumerate(file): #enumerate used to obtain line numbers and thus node numbers
            coords = line.rsplit()[0].split(",")
            x = int(coords[0])
            y = int(coords[1])
            nodes.append(Node(x,y))
    elif (ext == "tsp"):
        # If .tsp then the format of the file changes and needs to be read differently.
        file.readline()
        file.readline()
        file.readline()
        no_nodes = int(file.readline().strip().split()[1])
        file.readline()
        file.readline()
        file.readline()

        for i in range(0, no_nodes):

            coords = file.readline().strip().split()[1:]
            x = float(coords[0])
            y = float(coords[1])

            nodes.append(Node(x,y))

    return nodes

@app.route('/')
def load_home():
    # Loads the home page
    return render_template('index.html', instances = INSTANCES, async_mode=socketio.async_mode)

@app.route('/about')
def load_about():
    # Loads the about page
    return render_template('about.html')

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    socketio.run(app)
