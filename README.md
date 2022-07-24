# Asteroids-with-NEAT-python

My implementation of the NEAT algorithm using python into the arcade game asteroids that I built. The neural networks are fed the position of the nearest asteroid in polar coordinates relative to the ship and its direction.

## Dependencies

- Python 3+

## Getting Started

1. Clone the repo:

```bash 
git clone https://github.com/finnformica/Asteroids-with-NEAT-python
```

2. Install the requirements:

```bash

# change into working directory
cd /.../Asteroids-with-NEAT-python/

# setup virtual environment
python3 -m venv venv
source venv/bin/activate

# install requirements
pip3 install requirements.txt
```
3. Run the main file:

```bash
python3 main.py
```

A pygame window should then open with the Asteroid game running and a Neural Network playing the game.
