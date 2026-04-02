import json
import plotly.graph_objects as go

def loadLocations(path):
    with open(path, "r") as f:
        return json.load(f)

def isSquare(key):
    return len(key) == 2 and key[0].isalpha() and key[1].isdigit()

def extractData(data):
    bx, by, bz = [], [], []
    sx, sy, sz = [], [], []

    for key, value in data.items():
        if isSquare(key):
            bx.append(value["x"])
            by.append(value["y"])
            bz.append(value["z"])
        else:
            for obj in value:
                sx.append(obj["x"])
                sy.append(obj["y"])
                sz.append(obj["z"])

    return (bx, by, bz), (sx, sy, sz)

def plot(locations):
    fig = go.Figure()

    # white
    (bx, by, bz), (sx, sy, sz) = extractData(locations["white"])
    fig.add_trace(go.Scatter3d(x=bx, y=by, z=bz,
                               mode='markers',
                               marker=dict(size=3, color='blue'),
                               name='White board'))

    fig.add_trace(go.Scatter3d(x=sx, y=sy, z=sz,
                               mode='markers',
                               marker=dict(size=5, color='blue', symbol='diamond'),
                               name='White storage'))

    # black
    (bx, by, bz), (sx, sy, sz) = extractData(locations["black"])
    fig.add_trace(go.Scatter3d(x=bx, y=by, z=bz,
                               mode='markers',
                               marker=dict(size=3, color='red'),
                               name='Black board'))

    fig.add_trace(go.Scatter3d(x=sx, y=sy, z=sz,
                               mode='markers',
                               marker=dict(size=5, color='red', symbol='diamond'),
                               name='Black storage'))

    fig.update_layout(scene=dict(
        xaxis_title='X',
        yaxis_title='Y',
        zaxis_title='Z'
    ))
    fig.update_layout(
        scene=dict(
            aspectmode='cube'
        )
    )

    fig.show()

if __name__ == "__main__":
    locations = loadLocations(r"C:\Users\Jayda\PycharmProjects\Chester\testbed\testLocations.json")
    plot(locations)