from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/')
def main():
    return redirect('/index_Main')

@app.route('/index_Main')
def index_Main():
    return render_template('Milestone_Main.html')

if __name__ == '__main__':
    app.run(host='159.203.65.80',port=33507)
