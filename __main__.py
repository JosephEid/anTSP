from flask import Flask
from flask import request
from flask import render_template
from flask import send_file
import io
import random
from flask import Response, redirect, url_for
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import itertools
import time
import sys

from graph import Node, Graph

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
dir = os.path.dirname(os.path.realpath(__file__))
INSTANCES = [x for x in os.listdir(dir+'/instances/')]

global output_message
output_message = "Useful Text will appear here"

def update_message(message):
    print("you here")
    global output_message
    output_message = message

@app.route('/plotcustom.png')
def solve_custom():
    print("you here")
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

    coords = request.args.get('custom_coords')
    coords = str(coords)
    coords = coords.split(':')
    coords.pop(len(coords)-1)
    nodes = []
    for i in coords:
        i = i.strip("()")
        vals = i.split(",")
        x = float(vals[0])
        y = float(vals[1])
        nodes.append(Node(x,y))


    graph = Graph(nodes, alpha, beta, pec)

    (fig, distance) = solver("Custom", graph, generations, nodes)

    recent_dist = distance
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/custompreview.png')
def custom_preview_png():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    coords = request.args.get('custom_coords')
    coords = str(coords)
    coords = coords.split(':')
    coords.pop(len(coords)-1)
    print(coords)
    for i in coords:
        i = i.strip("()")
        vals = i.split(",")
        print(vals)
        x = float(vals[0])
        print(x)
        y = float(vals[1])
        axis.text(x,y, str(i))
        axis.scatter(x, y, c = 'b', label = str(i))

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/plotoptimum.png')
def plot_optimum_png():
    instance = request.args.get('prev_instance')
    instance = str(instance)
    file_name = os.path.splitext(instance)[0]
    print(str(file_name))
    optimal_found = os.path.isfile(dir+'/optimals/'+str(file_name)+'.opt.tour')
    if optimal_found:
        print("yeaboifound")
        fig = create_optimal(file_name)
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

def create_optimal(file_name):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    dir = os.path.dirname(os.path.realpath(__file__))
    optimal_file = open(dir+'/optimals/'+file_name+'.opt.tour')
    file = open(dir+'/instances/'+file_name+'.tsp')
    optimal_file.readline()
    optimal_file.readline()
    optimal_file.readline()
    optimal_file.readline()
    optimal_file.readline()
    optimal_path = optimal_file.readline()
    optimal_path = optimal_path.split()
    optimal_path = [int(n) - 1 for n in optimal_path]
    nodes = [] #Array storing nodes

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

    axis.set_title(file_name + ' optimal path')
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
    instance = request.args.get('prev_instance')
    instance = str(instance)
    fig = create_preview(instance)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_preview(instance):
    file_type = os.path.splitext(instance)[1]

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    dir = os.path.dirname(os.path.realpath(__file__))
    file = open(dir+'/instances/'+instance)
    nodes = [] #Array storing nodes
    if file_type == '.csv':

        for nodeNo,line in enumerate(file): #enumerate used to obtain line numbers and thus node numbers
            coords = line.rsplit()[0].split(",")

            x = int(coords[0])
            y = int(coords[1])
            axis.scatter(x, y, c = 'b', label = nodeNo)
            axis.set_title(instance)
            axis.text(x+5,y+5, str(nodeNo))
            nodes.append(Node(x,y))
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
            axis.set_title(instance)
            axis.text(x,y, str(i))
            nodes.append(Node(x,y))

    return fig

@app.route('/plot.png')
def plot_png():
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
    instance = request.args.get('instance')
    instance = str(instance)
    (fig, distance) = create_figure(alpha, beta, instance, generations, q, pec)
    recent_dist = distance
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_figure(alpha, beta, instance, generations, q, pec):
    dir = os.path.dirname(os.path.realpath(__file__))
    file = open(dir+'/instances/'+instance)
    nodes = [] #Array storing nodes

    for nodeNo,line in enumerate(file): #enumerate used to obtain line numbers and thus node numbers
        coords = line.rsplit()[0].split(",")
        x = int(coords[0])
        y = int(coords[1])
        nodes.append(Node(x,y))
    graph = Graph(nodes, alpha, beta, pec)

    return solver(instance, graph, generations, nodes)

def solver(instance_name, graph, generations, nodes):

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)

    path, distance = graph.find_shortest_path(generations)
    axis.set_title(instance_name + " - Distance: "+ str(distance))

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

    return (fig, distance)

@app.route('/')
def load_home():

    if request.headers.get('accept') == 'text/event-stream':
        def events():
            for i, c in enumerate(itertools.cycle('\|/-')):
                yield "data: %s \n\n" % (output_message)
                time.sleep(.1)  # an artificial delay
        return Response(events(), content_type='text/event-stream')
    return render_template('index.html', instances = INSTANCES)
    #return render_template('index.html', instances = INSTANCES)

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    app.run(threaded=True)
