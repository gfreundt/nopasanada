from flask import Flask, request

app = Flask(__name__)


@app.route("/search")
def search():
    # To get all query parameters as a dictionary
    all_params = request.args.to_dict()

    return f"All params: {all_params}"


if __name__ == "__main__":
    app.run(debug=True)
