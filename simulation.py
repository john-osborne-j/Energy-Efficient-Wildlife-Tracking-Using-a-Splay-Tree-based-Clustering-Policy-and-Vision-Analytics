import math
import random
from collections import defaultdict

# --- Configuration (Defaults) ---
AREA_SIZE = 1000.0
N_CLUSTERS = 5
T_MAX = 30
ALPHA = 0.5; BETA = 0.3; KAPPA = 0.1; ZETA = 0.1

def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])

class Node:
    def __init__(self, idx, pos, cluster):
        self.idx = idx; self.pos = pos; self.cluster = int(cluster)
        self.batt = 100.0; self.dead = False; self.S = 0.0; self.fair = 0.0
        self.is_head = False; self.head_since = 0
        self.dead_since = None

    def get_color(self):
        if self.dead: return '#ff0000' # Red
        if self.batt > 50: return '#00ff00' # Green
        if self.batt > 20: return '#ffff00' # Yellow
        return '#ff9900' # Orange

    def consume(self, amount, sim_time):
        if self.dead: return
        self.batt -= amount
        if self.batt <= 0: 
            self.batt = 0; self.dead = True; self.is_head = False
            self.dead_since = sim_time

def calculate_utility(node, gateway):
    term_S = min(node.S, 1.0); term_E = node.batt / 100.0
    term_fair = min(node.fair, 1.0)
    d_gate = dist(node.pos, gateway)
    term_lq = 1.0 - (d_gate / (AREA_SIZE * 1.414))
    return ALPHA*term_S + BETA*term_E + KAPPA*term_fair + ZETA*term_lq

class Simulation:
    def __init__(self, n_nodes=50):
        self.n_nodes = n_nodes
        self.rng = random.Random() # New random instance
        self.nodes = []
        self.clusters = defaultdict(list)
        self.current_heads = {}
        self.sim_time = 0
        self.gateway = (AREA_SIZE/2, AREA_SIZE/2)
        self.reset(n_nodes)

    def reset(self, n_nodes):
        self.n_nodes = int(n_nodes)
        self.sim_time = 0
        
        # Setup Network
        centers = [(self.rng.uniform(100, AREA_SIZE-100), self.rng.uniform(100, AREA_SIZE-100)) for _ in range(N_CLUSTERS)]
        self.nodes = []
        for i in range(self.n_nodes):
            c_idx = self.rng.randint(0, N_CLUSTERS-1)
            cx, cy = centers[c_idx]
            nx = cx + self.rng.gauss(0, 80)
            ny = cy + self.rng.gauss(0, 80)
            pos = (max(0, min(AREA_SIZE, nx)), max(0, min(AREA_SIZE, ny)))
            self.nodes.append(Node(i, pos, c_idx))

        self.clusters = defaultdict(list)
        for n in self.nodes: self.clusters[n.cluster].append(n)
        self.current_heads = {c: None for c in self.clusters}

    def step(self):
        # Run logic 1x per frame to slow down backend progression too, or keep it 3x? 
        # User said "simulation is going really fast", often better to slow down updates.
        # Let's reduce internal ticks to 1 per step call as well.
        for _ in range(1):
            self._run_simulation_step()
        
        return self.get_state()

    def _run_simulation_step(self):
        self.sim_time += 1
        ev_pos = (self.rng.uniform(0, AREA_SIZE), self.rng.uniform(0, AREA_SIZE))

        for n in self.nodes:
            if n.dead: continue
            n.consume(0.2, self.sim_time)
            n.S *= 0.9
            if not n.is_head: n.fair += 0.02
            if dist(n.pos, ev_pos) < 150: n.S += 0.8; n.consume(0.5, self.sim_time)

        for c_id, members in self.clusters.items():
            head = self.current_heads.get(c_id)
            if head is None or head.dead or (head and (self.sim_time - head.head_since) > T_MAX):
                candidates = [n for n in members if not n.dead]
                if candidates:
                    winner = max(candidates, key=lambda n: calculate_utility(n, self.gateway))
                    if head and head != winner: head.is_head = False
                    self.current_heads[c_id] = winner; winner.is_head = True
                    winner.head_since = self.sim_time; winner.fair = 0.0; winner.consume(1.5, self.sim_time)

    def get_state(self):
        # Return serializable state
        nodes_data = []
        links = []
        dead_nodes_stats = []
        
        for n in self.nodes:
            color = n.get_color()
            
            # Logic for links: if not head, link to head
            if not n.is_head and not n.dead:
                head = self.current_heads.get(n.cluster)
                if head and not head.dead:
                    links.append({
                        'start': n.pos,
                        'end': head.pos
                    })
            
            if n.dead:
                downtime = self.sim_time - n.dead_since if n.dead_since is not None else 0
                dead_nodes_stats.append({
                    'id': n.idx,
                    'dead_since': n.dead_since,
                    'downtime': downtime
                })

            nodes_data.append({
                'id': n.idx,
                'x': n.pos[0],
                'y': n.pos[1],
                'color': color,
                'is_head': n.is_head,
                'dead': n.dead,
                'batt': n.batt,
                'cluster': n.cluster
            })
            
        return {
            'sim_time': self.sim_time,
            'gateway': self.gateway,
            'nodes': nodes_data,
            'links': links,
            'dead_stats': dead_nodes_stats
        }
