# Message Passing on WVS Belief Networks
## Mathematical Foundations · Algorithms · Interpretations · Pitfalls

---

## Preface: What This Document Covers

This document details a complete message passing framework for propagating
belief states through World Values Survey construct networks. Each section
covers one algorithmic stage: its mathematical motivation, what it computes,
how to interpret the output in substantive terms, the pitfalls specific to
survey data, and working Python code.

The framework is organized around four propagation regimes:

1. **Within-network belief propagation** — how evidence at one construct
   implies distributions over others within a single country
2. **Spectral diffusion** — how beliefs spread across the network over
   continuous "diffusion time"
3. **Influence mapping via Personalized PageRank** — which constructs
   dominate downstream belief space
4. **Two-layer multilayer propagation** — how belief shifts in one country
   imply changes in another, mediated by the GW transport alignment
5. **Temporal dynamics** — using the network as a generative model of
   belief evolution across waves
6. **Curvature-weighted opinion dynamics** — how Ricci curvature shapes
   the velocity and direction of belief change

Each stage builds on the previous. The TDA pipeline (v2) is assumed to have
already run, producing weight matrices, distance matrices, Floyd-Warshall
results, Ricci curvature matrices, and GW transport plans.

---

## Conceptual Map

```
Observed belief state (evidence at some constructs)
              │
              ▼
    ┌─────────────────────┐
    │  Within-network BP  │ ← edge potentials from w(i,j)
    │  (factor graph)     │
    └────────┬────────────┘
             │ posterior beliefs over all constructs
             ▼
    ┌─────────────────────┐
    │  Spectral diffusion │ ← Laplacian eigenmodes
    │  (heat equation)    │
    └────────┬────────────┘
             │ smooth propagation, modal decomposition
             ▼
    ┌─────────────────────┐
    │  PageRank influence │ ← random walk on construct graph
    │  mapping            │
    └────────┬────────────┘
             │ influence scores per construct
             ▼
    ┌─────────────────────────────────┐
    │  Two-layer multilayer MP        │ ← GW transport plan
    │  (construct × country)          │   links layers
    └────────┬────────────────────────┘
             │ cross-country belief propagation
             ▼
    ┌─────────────────────┐
    │  Temporal dynamics  │ ← wave-indexed adjacency
    │  (Graph RNN)        │
    └────────┬────────────┘
             │ forecasted belief states
             ▼
    ┌──────────────────────────────┐
    │  Curvature-weighted dynamics │ ← Ricci κ(i,j)
    │  (opinion dynamics on       │
    │   the gamma surface)        │
    └──────────────────────────────┘
              │
              ▼
    Velocity field on belief manifold
    (where beliefs flow fast/slow/amplify/dampen)
```

---

## Stage 1: Within-Network Belief Propagation

### 1.1 Mathematical Motivation

Your construct network encodes a **Markov random field (MRF)**: a joint
distribution over belief states where the conditional independence structure
matches the graph. Specifically, each construct i is conditionally independent
of all non-neighbors given its direct neighbors — the **Markov blanket**
property.

The joint distribution factorizes as:

$$P(\mathbf{x}) \propto \prod_{i \in V} \phi_i(x_i)
\prod_{(i,j) \in E} \psi_{ij}(x_i, x_j)$$

where:

- **Node potential** φᵢ(xᵢ): the prior marginal distribution of construct i
  responses. For Likert-scale items, this is a categorical distribution over
  {1,2,3,4,5} estimated from marginal frequencies.

- **Edge potential** ψᵢⱼ(xᵢ, xⱼ): the compatibility of states xᵢ and xⱼ
  given the empirical weight w(i,j). For a linear-Gaussian approximation:

$$\psi_{ij}(x_i, x_j) = \exp\!\left(-\frac{(x_i - w_{ij} x_j)^2}{2\sigma^2}\right)$$

  For categorical/ordinal data, a **Potts model** is more appropriate:

$$\psi_{ij}(x_i, x_j) = \exp\!\left(J_{ij} \cdot \mathbb{1}[x_i = x_j]\right)$$

  where $J_{ij} = \beta \cdot |w_{ij}|$ and $\beta$ is an inverse-temperature
  parameter controlling coupling strength.

**Belief propagation (BP)** computes the exact marginal posteriors in trees,
and approximate marginals in loopy graphs, by passing **messages** between
neighboring nodes. The message $m_{i \to j}^{(t)}(x_j)$ represents node i's
estimate of j's marginal given all information available to i except from j:

$$m_{i \to j}^{(t+1)}(x_j) = \sum_{x_i} \psi_{ij}(x_i, x_j)\, \phi_i(x_i)
\prod_{k \in \mathcal{N}(i) \setminus j} m_{k \to i}^{(t)}(x_i)$$

After convergence (or max iterations), the **belief** at node i is:

$$b_i(x_i) \propto \phi_i(x_i) \prod_{k \in \mathcal{N}(i)} m_{k \to i}(x_i)$$

### 1.2 Substantive Interpretation

Given evidence that a survey respondent strongly agrees with construct A
(e.g., "I trust national institutions"), BP computes the **implied posterior
distribution** over all other constructs. This answers:

- *If someone distrusts institutions, what else are they likely to believe
  about democracy, government, interpersonal trust, and religion?*
- *Which constructs are most constrained by knowing the state of construct A?*
- *Which constructs remain nearly at their prior — i.e., are belief-independent
  of the evidence node?*

The ratio b_i(x_i) / φᵢ(xᵢ) is a **lift** — how much knowing A shifted the
distribution at i. High lift nodes are the constructs most implied by the
evidence.

### 1.3 Pitfalls

**Loopy graphs break exact inference.** WVS construct networks are highly
cyclic. Loopy BP is an approximation — it may not converge, or may converge
to incorrect marginals. In practice: run for a fixed number of iterations,
monitor message norm change, and treat results as soft evidence rather than
exact posteriors.

**The Gaussian approximation distorts ordinal data.** Likert scales are
not continuous. Using a Gaussian edge potential treats the distance between
"strongly agree" and "agree" as equal to the distance between "agree" and
"neutral" — which is empirically false. Use categorical potentials when
response distributions are non-symmetric.

**Edge weights are not sufficient statistics.** Your weights capture the
monotonic strength of the i→j relationship, but BP requires a full conditional
distribution p(xⱼ | xᵢ). The weight alone specifies only the mean of this
conditional, not its shape. Estimate the full conditional from your data if
available.

**Directed edges require a directed graphical model (BN, not MRF).** If
you want to respect directionality, you need a Bayesian network (DAG), which
requires acyclicity. Your network has cycles, so you must either symmetrize
(losing direction) or use loopy belief propagation on a directed model
(technically unsound but often practical).

### 1.4 Python Implementation

```python
import numpy as np
from typing import Dict, List, Optional, Tuple


class BeliefPropagator:
    """
    Loopy belief propagation on a WVS construct network.
    Supports Gaussian (continuous) and Potts (categorical/ordinal) potentials.
    """

    def __init__(
        self,
        W: np.ndarray,                    # k×k weight matrix
        node_priors: np.ndarray,          # k×S array: prior P(xi=s) for each node
        potential_type: str = 'gaussian', # 'gaussian' or 'potts'
        beta: float = 1.0,               # inverse temperature (Potts)
        sigma: float = 0.5,              # noise scale (Gaussian)
        max_iter: int = 100,
        tol: float = 1e-6,
        damping: float = 0.5,            # message damping for stability
    ):
        self.W = W
        self.k = W.shape[0]
        self.priors = node_priors        # shape (k, n_states)
        self.n_states = node_priors.shape[1]
        self.potential_type = potential_type
        self.beta = beta
        self.sigma = sigma
        self.max_iter = max_iter
        self.tol = tol
        self.damping = damping

        # Build edge list from nonzero weights
        self.edges = [
            (i, j) for i in range(self.k)
            for j in range(self.k)
            if i != j and abs(W[i, j]) > 0
        ]
        self.neighbors = {
            i: [j for j2, j in self.edges if j2 == i] +
               [j2 for j2, j in self.edges if j == i and j2 != i]
            for i in range(self.k)
        }
        # Deduplicate
        self.neighbors = {i: list(set(v)) for i, v in self.neighbors.items()}

    def _edge_potential(self, i: int, j: int) -> np.ndarray:
        """
        Compute S×S edge potential matrix ψ(xi, xj).
        Entry [s, t] = ψ(xi=s, xj=t).
        """
        S = self.n_states
        states = np.arange(S, dtype=float)
        w = self.W[i, j]

        if self.potential_type == 'gaussian':
            # ψ(xi, xj) = exp(-(xi - w*xj)^2 / (2σ²))
            xi = states[:, None]   # (S,1)
            xj = states[None, :]   # (1,S)
            psi = np.exp(-((xi - w * xj) ** 2) / (2 * self.sigma ** 2))

        elif self.potential_type == 'potts':
            # ψ(xi, xj) = exp(β|w| * 1[xi==xj]) if w>0
            #           = exp(β|w| * 1[xi≠xj]) if w<0 (anti-ferromagnetic)
            J = self.beta * abs(w)
            if w >= 0:
                # Agreement favored
                psi = np.where(
                    np.equal.outer(states.astype(int), states.astype(int)),
                    np.exp(J), 1.0
                )
            else:
                # Disagreement favored (inverse relationship)
                psi = np.where(
                    np.equal.outer(states.astype(int), states.astype(int)),
                    1.0, np.exp(J)
                )
        else:
            raise ValueError(f"Unknown potential type: {self.potential_type}")

        return psi  # (S, S)

    def run(
        self,
        evidence: Optional[Dict[int, np.ndarray]] = None
    ) -> Tuple[np.ndarray, bool]:
        """
        Run loopy belief propagation.

        Parameters
        ----------
        evidence : dict mapping node index → observed distribution (length S)
                   Hard evidence: one-hot vector. Soft evidence: any distribution.

        Returns
        -------
        beliefs : (k, S) array of marginal beliefs at each node
        converged : whether messages converged within max_iter
        """
        S = self.n_states

        # Initialize messages uniformly
        messages = {}
        for (i, j) in self.edges:
            messages[(i, j)] = np.ones(S) / S

        # Apply evidence by modifying priors
        priors = self.priors.copy()
        if evidence:
            for node, obs in evidence.items():
                priors[node] = obs / (obs.sum() + 1e-12)

        converged = False
        for iteration in range(self.max_iter):
            new_messages = {}
            max_change = 0.0

            for (i, j) in self.edges:
                psi = self._edge_potential(i, j)   # (S,S): psi[xi, xj]

                # Incoming messages to i from all neighbors except j
                incoming = priors[i].copy()
                for k_node in self.neighbors[i]:
                    if k_node != j and (k_node, i) in messages:
                        incoming *= messages[(k_node, i)]
                incoming /= incoming.sum() + 1e-12

                # New message: sum over xi
                # m_{i→j}(xj) = Σ_{xi} ψ(xi,xj) * incoming(xi)
                new_msg = psi.T @ incoming   # (S,S).T @ (S,) = (S,)
                new_msg /= new_msg.sum() + 1e-12

                # Damping for stability
                if (i, j) in messages:
                    new_msg = (self.damping * new_messages.get((i,j), new_msg)
                               + (1 - self.damping) * new_msg)

                change = np.max(np.abs(new_msg - messages.get((i, j),
                                                              np.ones(S)/S)))
                max_change = max(max_change, change)
                new_messages[(i, j)] = new_msg

            messages = new_messages

            if max_change < self.tol:
                converged = True
                break

        # Compute final beliefs
        beliefs = np.zeros((self.k, S))
        for i in range(self.k):
            b = priors[i].copy()
            for k_node in self.neighbors[i]:
                if (k_node, i) in messages:
                    b *= messages[(k_node, i)]
            b /= b.sum() + 1e-12
            beliefs[i] = b

        return beliefs, converged

    def compute_lift(
        self,
        beliefs: np.ndarray,
    ) -> np.ndarray:
        """
        Lift = beliefs / prior. High lift = most affected by evidence.
        Returns (k,) array of KL divergence from prior to posterior.
        """
        prior = self.priors + 1e-12
        post  = beliefs + 1e-12
        # KL(posterior || prior) per node
        kl = np.sum(post * np.log(post / prior), axis=1)
        return kl

    def propagate_scenario(
        self,
        construct_idx: int,
        state_value: int,
        construct_labels: List[str],
        top_n: int = 10
    ) -> Dict:
        """
        High-level interface: inject hard evidence at one construct,
        return ranked list of most-affected other constructs.
        """
        S = self.n_states
        obs = np.zeros(S)
        obs[state_value] = 1.0

        beliefs, converged = self.run(evidence={construct_idx: obs})
        lift = self.compute_lift(beliefs)
        lift[construct_idx] = 0  # exclude the evidence node

        ranked = np.argsort(lift)[::-1][:top_n]
        return {
            'evidence_construct': construct_labels[construct_idx],
            'evidence_state': state_value,
            'converged': converged,
            'beliefs': beliefs,
            'lift': lift,
            'top_affected': [
                {
                    'construct': construct_labels[i],
                    'kl_from_prior': float(lift[i]),
                    'modal_state': int(np.argmax(beliefs[i])),
                    'posterior': beliefs[i].tolist()
                }
                for i in ranked
            ]
        }


# ── Usage ────────────────────────────────────────────────────────────────────

def demo_bp(W: np.ndarray, construct_labels: List[str]):
    """
    Demonstrate BP for a single country network.
    Assumes 5-point Likert scale (states 0..4).
    """
    k = W.shape[0]
    n_states = 5

    # Uniform priors (replace with empirical marginals if available)
    priors = np.ones((k, n_states)) / n_states

    bp = BeliefPropagator(
        W=W,
        node_priors=priors,
        potential_type='potts',
        beta=2.0,
        max_iter=200,
        damping=0.5
    )

    # Scenario: construct 0 observed at maximum agreement (state=4)
    result = bp.propagate_scenario(
        construct_idx=0,
        state_value=4,
        construct_labels=construct_labels,
        top_n=10
    )

    print(f"Evidence: {result['evidence_construct']} = strongly agree")
    print(f"Converged: {result['converged']}")
    print(f"\nTop affected constructs:")
    for r in result['top_affected']:
        print(f"  {r['construct']:40s}  KL={r['kl_from_prior']:.4f}  "
              f"modal_state={r['modal_state']}")

    return result
```

---

## Stage 2: Spectral Diffusion

### 2.1 Mathematical Motivation

The **graph Laplacian** is the central operator of network dynamics. Define:

$$L = D - A$$

where D is the diagonal degree matrix (Dᵢᵢ = Σⱼ wᵢⱼ) and A is the weighted
adjacency matrix. The normalized Laplacian is:

$$\mathcal{L} = D^{-1/2} L D^{-1/2}$$

The **heat equation on the graph** describes how a belief state x(0) diffuses:

$$\frac{d\mathbf{x}}{dt} = -L\mathbf{x}(t)$$

The solution is the **heat kernel**:

$$\mathbf{x}(t) = e^{-Lt}\mathbf{x}(0) = \sum_{k=0}^{n-1} e^{-\lambda_k t}
\langle \mathbf{x}(0), \mathbf{u}_k \rangle\, \mathbf{u}_k$$

where λₖ are the eigenvalues of L and uₖ are the corresponding eigenvectors.

This decomposition is the **spectral representation** of diffusion:
- Each eigenvector uₖ is a **mode of belief variation** — a spatial pattern
  across constructs
- Each eigenvalue λₖ is its **diffusion rate** — how quickly that pattern
  decays
- Small λₖ (slow decay) = global, large-scale patterns that persist
- Large λₖ (fast decay) = local, fine-grained patterns that dissipate quickly

The **diffusion distance** between two constructs i and j at time t is:

$$D_t(i, j) = \left\| e^{-Lt/2}(e_i - e_j) \right\|^2
= \sum_k e^{-\lambda_k t} (u_k(i) - u_k(j))^2$$

This is a multi-scale metric: at small t it resembles geodesic distance;
at large t it collapses to global community structure.

### 2.2 Substantive Interpretation

The eigendecomposition of L gives you the **natural basis of belief variation**
in a country:

- **Eigenvector u₁** (λ₁ = 0 always): the constant mode — all constructs
  moving together. A shift in this direction is a uniform global belief change,
  like a general rise in life satisfaction.

- **Eigenvector u₂** (Fiedler vector, λ₂ smallest nonzero): the slowest
  non-trivial diffusion mode. This separates constructs into two groups that
  vary most independently — the principal axis of belief variation in this
  country. The constructs with opposite signs in u₂ are the ones that most
  reliably vary in opposite directions.

- **Higher eigenvectors**: increasingly local patterns of belief variation.

The **heat kernel at time t** smooths beliefs at a specific scale. Small t
preserves local detail; large t shows only global structure. Sweeping t from 0
to ∞ is a multi-scale analysis of how beliefs spread — directly analogous to
the ε-sweep in TDA but for dynamics rather than topology.

The **diffusion map** — embedding constructs using (e^{-λ₂t} u₂,
e^{-λ₃t} u₃, ...) — places constructs close together if they are
dynamically similar: they receive similar information from any diffusing
signal.

### 2.3 Pitfalls

**The Laplacian assumes undirected diffusion.** Your edges are directed.
The standard Laplacian symmetrizes the graph, losing directional information.
For directed diffusion, use the **non-symmetric Laplacian** L = D_out - W,
where D_out uses out-degree. Its left and right eigenvectors are different —
the right eigenvectors describe how mass spreads forward; the left describe
where mass accumulates. This is more complex but substantively richer.

**Diffusion time t is a free parameter.** There is no canonical choice of t.
The **optimal scale** for your question depends on what you want to see:
short t for local propagation, long t for global. Sweep t and use the
diffusion distance as a multi-scale distance metric in TDA rather than
committing to one value.

**Zero eigenvalues indicate disconnected components.** If β₀ > 1 (multiple
persistent connected components from your TDA), L has multiple zero
eigenvalues. Diffusion does not cross component boundaries. Run diffusion
separately per component or use a weakly connected approximation.

**The heat equation is linear.** Real belief dynamics are not. Normative
pressures, threshold effects, and social influence produce nonlinear dynamics.
The heat equation is an approximation valid for small perturbations around
equilibrium. For large shocks, use nonlinear dynamics (Stage 6).

### 2.4 Python Implementation

```python
import numpy as np
from scipy.linalg import eigh
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt


class SpectralDiffusion:
    """
    Spectral analysis and heat diffusion on a construct network.
    """

    def __init__(self, W: np.ndarray, normalized: bool = True):
        """
        Parameters
        ----------
        W : symmetric weight matrix (symmetrized from directed weights)
        normalized : use normalized Laplacian (recommended for varying degrees)
        """
        W_sym = (np.abs(W) + np.abs(W).T) / 2
        np.fill_diagonal(W_sym, 0)
        self.W = W_sym
        self.k = W_sym.shape[0]
        self.normalized = normalized

        # Build Laplacian
        deg = W_sym.sum(axis=1)
        D   = np.diag(deg)
        L   = D - W_sym

        if normalized:
            D_inv_sqrt = np.diag(1.0 / np.sqrt(deg + 1e-12))
            L = D_inv_sqrt @ L @ D_inv_sqrt

        self.L = L

        # Eigendecomposition (all eigenvalues — L is symmetric PSD)
        self.eigenvalues, self.eigenvectors = eigh(L)
        # Clip small negatives from numerical error
        self.eigenvalues = np.maximum(self.eigenvalues, 0)

    def heat_kernel(self, t: float) -> np.ndarray:
        """
        Compute heat kernel H(t) = exp(-Lt).
        H(t)[i,j] = probability that a random walker starting at i
        is at j after diffusion time t.
        Returns (k,k) matrix.
        """
        decay = np.exp(-self.eigenvalues * t)
        return (self.eigenvectors * decay[None, :]) @ self.eigenvectors.T

    def diffuse(
        self,
        x0: np.ndarray,
        t: float
    ) -> np.ndarray:
        """
        Diffuse initial belief state x0 for time t.
        x0 : (k,) initial state vector (e.g., deviation from mean response)
        Returns (k,) diffused state.
        """
        H = self.heat_kernel(t)
        return H @ x0

    def diffusion_distance(
        self,
        t: float
    ) -> np.ndarray:
        """
        Pairwise diffusion distance matrix at time t.
        D_t(i,j)² = sum_k exp(-2λk t) (uk(i) - uk(j))²
        Returns (k,k) distance matrix.
        """
        # Scaled eigenvectors
        decay = np.exp(-self.eigenvalues * t)
        U_scaled = self.eigenvectors * decay[None, :]  # (k, k)

        # Pairwise squared distances
        diff = U_scaled[:, None, :] - U_scaled[None, :, :]  # (k,k,k)
        D_t = np.sqrt(np.sum(diff**2, axis=2))
        return D_t

    def diffusion_map(
        self,
        t: float,
        n_components: int = 3
    ) -> np.ndarray:
        """
        Diffusion map embedding: constructs as points in diffusion space.
        Uses top n_components non-trivial eigenvectors.
        Returns (k, n_components) embedding.
        """
        # Skip zero eigenvalue (index 0 if connected)
        n_zero = np.sum(self.eigenvalues < 1e-8)
        decay  = np.exp(-self.eigenvalues[n_zero:] * t)
        coords = self.eigenvectors[:, n_zero:n_zero + n_components] * decay[:n_components]
        return coords

    def fiedler_analysis(
        self,
        construct_labels: List[str]
    ) -> Dict:
        """
        Analyze the Fiedler vector (u₂): principal axis of belief variation.
        Returns partition of constructs into two groups.
        """
        n_zero  = np.sum(self.eigenvalues < 1e-8)
        fiedler = self.eigenvectors[:, n_zero]    # first nontrivial eigenvector
        fiedler_val = self.eigenvalues[n_zero]

        pos_group = [construct_labels[i] for i in range(self.k) if fiedler[i] > 0]
        neg_group = [construct_labels[i] for i in range(self.k) if fiedler[i] <= 0]

        ranked = np.argsort(np.abs(fiedler))[::-1]

        return {
            'fiedler_value':     float(fiedler_val),
            'fiedler_vector':    fiedler,
            'pos_group':         pos_group,   # constructs that vary together (+)
            'neg_group':         neg_group,   # constructs that vary together (-)
            'ranked_constructs': [construct_labels[i] for i in ranked],
            'participation':     fiedler[ranked].tolist(),
        }

    def scale_sweep(
        self,
        x0: np.ndarray,
        t_values: np.ndarray,
        construct_labels: List[str]
    ) -> np.ndarray:
        """
        Diffuse x0 across multiple time scales.
        Returns (len(t_values), k) array of diffused states.
        """
        results = np.zeros((len(t_values), self.k))
        for i, t in enumerate(t_values):
            results[i] = self.diffuse(x0, t)
        return results

    def plot_eigenspectrum(self, ax=None):
        """Plot eigenvalue spectrum — reveals network's diffusion structure."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))
        ax.stem(self.eigenvalues, markerfmt='C0o', linefmt='C0-', basefmt='k-')
        ax.axvline(x=np.sum(self.eigenvalues < 1e-8) - 0.5,
                   color='red', linestyle='--', alpha=0.5,
                   label='Zero eigenvalue boundary')
        ax.set_xlabel('Eigenvalue index')
        ax.set_ylabel('λ (diffusion rate)')
        ax.set_title('Laplacian Spectrum — Diffusion Rates of Belief Modes')
        ax.legend()
        return ax


# ── Usage ────────────────────────────────────────────────────────────────────

def demo_diffusion(W: np.ndarray, construct_labels: List[str]):
    sd = SpectralDiffusion(W, normalized=True)

    # Fiedler analysis: principal belief axis
    fiedler = sd.fiedler_analysis(construct_labels)
    print(f"Fiedler value (algebraic connectivity): {fiedler['fiedler_value']:.4f}")
    print(f"  High-side group: {fiedler['pos_group'][:5]}")
    print(f"  Low-side group:  {fiedler['neg_group'][:5]}")

    # Diffuse a shock: construct 0 is +1 standard deviation above mean
    x0 = np.zeros(len(construct_labels))
    x0[0] = 1.0

    t_values = np.logspace(-2, 2, 50)
    trajectory = sd.scale_sweep(x0, t_values, construct_labels)

    print(f"\nDiffusion trajectory shape: {trajectory.shape}")
    print(f"  At t=0.01: max affected = {construct_labels[np.argmax(trajectory[0])]}")
    print(f"  At t=10.0: max affected = {construct_labels[np.argmax(trajectory[-1])]}")

    # Diffusion map at intermediate scale
    dmap = sd.diffusion_map(t=1.0, n_components=3)
    print(f"\nDiffusion map embedding: {dmap.shape}")

    return sd, fiedler, trajectory, dmap
```

---

## Stage 3: Influence Mapping via Personalized PageRank

### 3.1 Mathematical Motivation

**Personalized PageRank (PPR)** answers a structurally different question
than diffusion: instead of "how does a single pulse spread?", it asks "what
is the steady-state influence of node i on the rest of the network under
continuous random restarts?"

Define the transition matrix P = D⁻¹W (row-normalized adjacency). The
PPR vector seeded at node i is:

$$\pi^{(i)} = \alpha\, e_i + (1 - \alpha)\, P^\top \pi^{(i)}$$

Solving:

$$\pi^{(i)} = \alpha\, (I - (1-\alpha) P^\top)^{-1} e_i$$

The scalar πⱼ^(i) measures how much of a random walker's steady-state
probability mass, starting from i with teleportation probability α back
to i, ends up at j. This is a measure of **structural influence**: how
much does i "reach" j through the network?

The full **PPR matrix** Π (k×k) where column i = π^(i) gives pairwise
influence scores. Πⱼᵢ is the influence of i on j.

The **influence asymmetry** Πⱼᵢ - Πᵢⱼ tells you whether the i→j
relationship is symmetric or one-directional in its influence.

### 3.2 Substantive Interpretation

PPR gives you the **sphere of influence** of each construct:

- **High Πⱼᵢ for many j**: construct i is a *belief hub* — shifts in i
  propagate broadly. These are the constructs where public opinion campaigns
  would have the largest multiplier effect.

- **Low Πⱼᵢ for all j**: construct i is a *belief sink* — it receives
  influence but doesn't propagate it. Isolated or peripheral beliefs.

- **High Πᵢⱼ but low Πⱼᵢ**: j influences i but not vice versa — j is
  upstream of i. In a causal reading, j is a driver; i is a consequence.

- **PPR on the country network**: replace the construct network with the
  country distance network. π^(MEX) gives the influence of Mexico's belief
  structure on all other countries — weighted by their network proximity.
  Countries with high PPR from multiple seeds are **belief attractors** —
  nodes that the global belief random walk tends to visit regardless of
  starting point.

### 3.3 Pitfalls

**PPR assumes a stationary distribution exists.** For this, the graph must
be strongly connected (for directed graphs) or connected (for undirected).
If your construct network has isolated components, PPR is undefined across
components — the teleportation parameter α effectively bridges them
artificially. Handle by running PPR per component.

**α controls locality vs. globality.** Small α (e.g., 0.05) = PPR spreads
widely, global influence. Large α (e.g., 0.85) = PPR stays local, nearby
influence. There is no canonical α. In web search (original PageRank),
α = 0.85 is conventional; for belief networks, α = 0.15–0.30 often gives
the most interpretable results. Sweep α and report sensitivity.

**PPR conflates reach with proximity.** A construct that is directly
connected to many others will have high PPR regardless of whether those
connections are strong or weak. Weighting the transition matrix by edge
strength (which you have) partially corrects this, but does not fully
separate influence from centrality.

**Influence ≠ causation.** PPR scores structural influence in the network
as you've measured it. High PPR for construct i does not mean i causally
drives j — it means i and j are structurally coupled. Causal inference
requires additional assumptions (temporal ordering, instrumental variables,
or do-calculus).

### 3.4 Python Implementation

```python
import numpy as np
from scipy.sparse.linalg import spsolve
from scipy.sparse import eye as speye, csr_matrix
from typing import List, Dict


class PPRInfluenceMapper:
    """
    Personalized PageRank influence mapping on construct or country networks.
    """

    def __init__(
        self,
        W: np.ndarray,
        alpha: float = 0.20,
        max_iter: int = 500,
        tol: float = 1e-8
    ):
        """
        Parameters
        ----------
        W : weight matrix (directed or symmetric)
        alpha : teleportation probability (restart probability)
        """
        self.k     = W.shape[0]
        self.alpha = alpha

        # Row-normalize to get transition matrix P
        W_abs  = np.abs(W)
        rs     = W_abs.sum(axis=1, keepdims=True)
        rs[rs == 0] = 1.0
        self.P = W_abs / rs       # (k,k) transition matrix, row-stochastic

    def ppr_vector(self, seed: int) -> np.ndarray:
        """
        Compute PPR vector for a single seed node using power iteration.
        π = α * e_seed + (1-α) * P^T π
        """
        pi = np.zeros(self.k)
        pi[seed] = 1.0
        e_seed = np.zeros(self.k)
        e_seed[seed] = 1.0

        for _ in range(500):
            pi_new = self.alpha * e_seed + (1 - self.alpha) * self.P.T @ pi
            if np.max(np.abs(pi_new - pi)) < 1e-8:
                break
            pi = pi_new

        return pi_new

    def full_ppr_matrix(self) -> np.ndarray:
        """
        Compute full k×k PPR matrix.
        Column i = PPR vector seeded at node i.
        Π[j,i] = influence of i on j.
        """
        Pi = np.zeros((self.k, self.k))
        for i in range(self.k):
            Pi[:, i] = self.ppr_vector(i)
        return Pi

    def influence_asymmetry(self, Pi: np.ndarray) -> np.ndarray:
        """
        Asymmetry matrix: A[j,i] = Pi[j,i] - Pi[i,j]
        Positive = i influences j more than j influences i.
        """
        return Pi - Pi.T

    def hub_scores(self, Pi: np.ndarray) -> np.ndarray:
        """
        Hub score for each node: sum of influence it exerts on all others.
        High score = broad influence.
        """
        return Pi.sum(axis=0) - np.diag(Pi)  # exclude self-influence

    def sink_scores(self, Pi: np.ndarray) -> np.ndarray:
        """
        Sink score: sum of influence received from all others.
        High score = strongly influenced by many.
        """
        return Pi.sum(axis=1) - np.diag(Pi)

    def analyze(self, construct_labels: List[str]) -> Dict:
        """Full PPR analysis with ranked outputs."""
        Pi   = self.full_ppr_matrix()
        asym = self.influence_asymmetry(Pi)
        hubs = self.hub_scores(Pi)
        sink = self.sink_scores(Pi)

        hub_rank  = np.argsort(hubs)[::-1]
        sink_rank = np.argsort(sink)[::-1]

        print("Top belief hubs (broadest influence):")
        for i in hub_rank[:5]:
            print(f"  {construct_labels[i]:40s}  hub_score={hubs[i]:.4f}")

        print("\nTop belief sinks (most influenced):")
        for i in sink_rank[:5]:
            print(f"  {construct_labels[i]:40s}  sink_score={sink[i]:.4f}")

        # Most asymmetric pairs
        asym_abs = np.abs(asym)
        np.fill_diagonal(asym_abs, 0)
        top_asym_idx = np.unravel_index(
            np.argsort(asym_abs.ravel())[::-1][:10],
            asym_abs.shape
        )

        print("\nMost asymmetric influence pairs (i→j dominates):")
        for j, i in zip(*top_asym_idx):
            if asym[j, i] > 0:
                print(f"  {construct_labels[i]:30s} → {construct_labels[j]:30s}"
                      f"  asymmetry={asym[j,i]:.4f}")

        return {
            'ppr_matrix':       Pi,
            'asymmetry':        asym,
            'hub_scores':       hubs,
            'sink_scores':      sink,
            'hub_ranking':      [construct_labels[i] for i in hub_rank],
            'sink_ranking':     [construct_labels[i] for i in sink_rank],
        }

    def influence_of_shift(
        self,
        seed_construct: int,
        shift_magnitude: float,
        Pi: np.ndarray,
        construct_labels: List[str]
    ) -> Dict:
        """
        Given a shift of `shift_magnitude` at one construct,
        compute implied first-order shifts at all others via PPR.
        """
        implied = Pi[:, seed_construct] * shift_magnitude
        ranked  = np.argsort(np.abs(implied))[::-1]
        return {
            'seed': construct_labels[seed_construct],
            'implied_shifts': {
                construct_labels[i]: float(implied[i])
                for i in ranked if i != seed_construct
            }
        }
```

---

## Stage 4: Two-Layer Multilayer Message Passing

### 4.1 Mathematical Motivation

A single country's belief network is Layer 1. The inter-country network
is Layer 2. These two layers are coupled by the **Gromov-Wasserstein
transport plan** T^(c₁,c₂), which maps constructs in country c₁ to
constructs in country c₂.

Formally, define:

- **Intra-layer adjacency** W^(c) for each country c (k×k construct network)
- **Inter-layer coupling** T^(c₁,c₂) (k×k transport plan from GW alignment)
- **Inter-country weight** d(c₁,c₂) = spectral distance (scalar)

The full **supra-adjacency matrix** of the multilayer system is:

$$\mathbf{W}^{\text{supra}} = \begin{pmatrix}
W^{(c_1)} & \omega_{12} T^{(c_1,c_2)} & \cdots \\
\omega_{21} T^{(c_2,c_1)} & W^{(c_2)} & \cdots \\
\vdots & & \ddots
\end{pmatrix}$$

where ωᵢⱼ = 1 / d(cᵢ,cⱼ) is the inter-country coupling strength (closer
countries couple more strongly).

Multilayer message passing on this supra-adjacency generalizes BP: messages
flow within each country's construct network AND between countries via the
GW transport coupling. A belief shift in construct A in country c₁ propagates:

1. Within c₁ via standard BP
2. Across to c₂ proportional to T^(c₁,c₂)[A, ·] — transferred to the
   constructs in c₂ that are functionally equivalent to A
3. Within c₂, the transferred signal further propagates

The **effective cross-country influence** of construct i in c₁ on construct j
in c₂ is:

$$\Pi^{(c_1 \to c_2)}_{ij} = \sum_k T^{(c_1,c_2)}_{ik}\, \Pi^{(c_2)}_{kj}
\cdot \omega_{c_1 c_2}$$

where Π^(c₂) is the within-country PPR matrix of c₂.

### 4.2 Substantive Interpretation

The two-layer system answers questions inaccessible to within-country
analysis alone:

- **"If institutional trust rises in Mexico, what happens in Brazil?"**
  The GW transport plan tells you which Brazilian construct receives the
  transferred signal; Brazil's PPR matrix tells you how it propagates.

- **"Which constructs are globally influential — not just within their
  country, but as signals that transfer and amplify across borders?"**
  These are constructs with high within-country hub score AND strong GW
  alignment to high-hub constructs in neighboring countries.

- **"Are there constructs with no cross-border equivalent?"**
  Constructs with diffuse GW transport plans (no single dominant mapping)
  are culturally specific — they exist in one country's belief space but
  have no functional counterpart elsewhere. These are the most interesting
  from a comparative theory standpoint.

- **"Which country pairs are most tightly belief-coupled?"**
  Country pairs with high ω (close spectral distance) AND concentrated
  GW transport plans (strong functional alignment) form **belief corridors**
  — geographic pathways of belief diffusion.

### 4.3 Pitfalls

**The GW transport plan is approximate.** Entropic GW with regularization
ε > 0 produces a smoothed transport plan where mass is spread more broadly
than the true optimal. Small ε = sharper alignment but slower convergence.
Interpret the transport plan probabilistically: T[i,j] is the probability
that construct i in c₁ corresponds to construct j in c₂, not a hard mapping.

**Multilayer BP on a dense supra-graph converges slowly.** If you include
all country pairs, the supra-adjacency has O(C² × k²) entries. For 80
countries and 200 constructs, this is ~256M entries — computationally
prohibitive for full BP. In practice: run multilayer MP only for subsets
of countries (e.g., a regional cluster from your between-network TDA) or
use a sparse approximation retaining only the top-k nearest neighbor
countries.

**Coupling strength ω is a modeling choice.** Using 1/d(c₁,c₂) is
one option. Alternatives: binary (threshold distance), Gaussian kernel
exp(-d²/σ²), or empirically estimated from observed belief comovement
across waves. Results can be sensitive to this choice.

**Cross-cultural construct equivalence is uncertain.** The GW transport plan
gives you functional equivalence under the assumption that network structure
encodes meaning. Two constructs are equivalent if they play the same structural
role. But this ignores semantic content — two constructs can be structurally
equivalent but mean entirely different things. Always validate transport plan
alignments against the actual construct content.

### 4.4 Python Implementation

```python
import numpy as np
from typing import Dict, List, Tuple, Optional


class MultilayerBeliefPropagator:
    """
    Two-layer message passing across construct networks of multiple countries,
    coupled via GW transport plans.
    """

    def __init__(
        self,
        country_weights: Dict[str, np.ndarray],      # country → W matrix
        transport_plans: Dict[Tuple[str,str], np.ndarray],  # (c1,c2) → T matrix
        country_distances: Dict[Tuple[str,str], float],      # (c1,c2) → distance
        alpha_teleport: float = 0.20,
        coupling_type: str = 'inverse',   # 'inverse', 'gaussian', 'binary'
        coupling_sigma: float = 1.0,      # for Gaussian coupling
        coupling_threshold: float = 0.5,  # for binary coupling
    ):
        self.countries = list(country_weights.keys())
        self.C = len(self.countries)
        self.k = next(iter(country_weights.values())).shape[0]

        self.W = country_weights
        self.T = transport_plans
        self.D = country_distances
        self.alpha = alpha_teleport

        # Compute inter-country coupling strengths ω(c1,c2)
        self.omega = self._build_coupling(coupling_type, coupling_sigma,
                                          coupling_threshold)

    def _build_coupling(self, ctype, sigma, threshold) -> Dict:
        omega = {}
        for c1 in self.countries:
            for c2 in self.countries:
                if c1 == c2:
                    omega[(c1, c2)] = 0.0
                    continue
                d = self.D.get((c1,c2), self.D.get((c2,c1), np.inf))
                if ctype == 'inverse':
                    omega[(c1,c2)] = 1.0 / (d + 1e-9)
                elif ctype == 'gaussian':
                    omega[(c1,c2)] = np.exp(-d**2 / (2 * sigma**2))
                elif ctype == 'binary':
                    omega[(c1,c2)] = 1.0 if d < threshold else 0.0
        return omega

    def _within_ppr(self, country: str) -> np.ndarray:
        """Within-country PPR matrix."""
        ppr = PPRInfluenceMapper(self.W[country], alpha=self.alpha)
        return ppr.full_ppr_matrix()

    def cross_country_influence(
        self,
        source_country: str,
        target_country: str,
        source_Pi: Optional[np.ndarray] = None,
        target_Pi: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Effective influence of constructs in source_country
        on constructs in target_country.
        Returns (k,k) matrix: [j,i] = influence of i in source on j in target.
        """
        pair = (source_country, target_country)
        pair_rev = (target_country, source_country)

        T = self.T.get(pair, self.T.get(pair_rev, None))
        if T is None:
            return np.zeros((self.k, self.k))

        if T.shape != (self.k, self.k):
            # Transpose if needed (GW may return T or T.T depending on order)
            T = T.T if T.shape == (self.k, self.k) else np.zeros((self.k, self.k))

        # Normalize transport plan (rows sum to 1/k by construction, but
        # numerical issues can arise)
        T_norm = T / (T.sum(axis=1, keepdims=True) + 1e-12)

        # Source PPR: how source constructs influence each other
        if source_Pi is None:
            source_Pi = self._within_ppr(source_country)

        # Target PPR: how injected signal propagates within target
        if target_Pi is None:
            target_Pi = self._within_ppr(target_country)

        w = self.omega.get((source_country, target_country), 0.0)

        # Cross-country influence:
        # T_norm maps source constructs → target constructs
        # target_Pi propagates within target
        # w scales by geographic coupling
        cross = w * (target_Pi @ T_norm @ source_Pi)
        return cross

    def propagate_scenario(
        self,
        evidence_country: str,
        evidence_construct: int,
        evidence_state: np.ndarray,   # (n_states,) distribution
        target_countries: Optional[List[str]] = None,
        construct_labels: Optional[List[str]] = None,
    ) -> Dict:
        """
        Full multilayer propagation scenario.
        Given evidence at one construct in one country, compute:
        1. Within-country posterior (BP)
        2. Cross-country implied shifts (multilayer PPR)
        3. Ranked construct-country pairs by implied change
        """
        if target_countries is None:
            target_countries = [c for c in self.countries if c != evidence_country]

        # Within-country BP
        priors = np.ones((self.k, 5)) / 5  # replace with empirical
        bp = BeliefPropagator(
            W=self.W[evidence_country],
            node_priors=priors,
            potential_type='potts',
            beta=2.0
        )
        evidence = {evidence_construct: evidence_state}
        beliefs_source, converged = bp.run(evidence=evidence)
        lift_source = bp.compute_lift(beliefs_source)

        # Source PPR
        source_Pi = self._within_ppr(evidence_country)

        # Cross-country propagation
        results = {
            'source_country':   evidence_country,
            'evidence_construct': evidence_construct,
            'source_beliefs':   beliefs_source,
            'source_lift':      lift_source,
            'source_converged': converged,
            'cross_country':    {}
        }

        for target in target_countries:
            target_Pi = self._within_ppr(target)
            cross_inf = self.cross_country_influence(
                evidence_country, target,
                source_Pi=source_Pi,
                target_Pi=target_Pi
            )

            # Column of cross_inf for source construct = implied influence
            implied = cross_inf[:, evidence_construct]
            ranked  = np.argsort(np.abs(implied))[::-1]

            results['cross_country'][target] = {
                'coupling': self.omega.get(
                    (evidence_country, target), 0.0
                ),
                'cross_influence_matrix': cross_inf,
                'implied_shifts': implied,
                'top_affected':   [
                    {
                        'construct': construct_labels[i] if construct_labels else str(i),
                        'implied_shift': float(implied[i])
                    }
                    for i in ranked[:5]
                ]
            }

        return results

    def belief_corridor_map(
        self,
        construct_idx: int,
        construct_labels: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        For a given construct, compute the C×C matrix of cross-country
        influence strengths. Entry [c2, c1] = how much construct in c1
        influences that construct (or its GW equivalent) in c2.
        """
        C = self.C
        corridor = np.zeros((C, C))

        for i, c1 in enumerate(self.countries):
            Pi_c1 = self._within_ppr(c1)
            for j, c2 in enumerate(self.countries):
                if i == j:
                    continue
                Pi_c2 = self._within_ppr(c2)
                cross = self.cross_country_influence(c1, c2, Pi_c1, Pi_c2)
                corridor[j, i] = cross[:, construct_idx].sum()

        return corridor
```

---

## Stage 5: Temporal Dynamics — The Network as a Generative Model

### 5.1 Mathematical Motivation

Across waves, the network adjacency W^(t) changes. The belief state
x^(t) — the vector of mean construct responses — also changes. The
question is whether the network dynamics at wave t **predict** the
belief state at wave t+1.

The simplest model is a **graph autoregression**:

$$\mathbf{x}^{(t+1)} = f\!\left(A^{(t)} \mathbf{x}^{(t)}\right) + \epsilon^{(t)}$$

where A^(t) = D^{-1}W^(t) is the row-normalized adjacency at wave t, f is
a nonlinear activation, and ε^(t) is an exogenous shock.

A richer model — **Graph Recurrent Network (Graph RNN)** — carries hidden
state:

$$\mathbf{h}^{(t+1)} = \sigma\!\left(W_h A^{(t)} \mathbf{h}^{(t)}
+ W_x \mathbf{x}^{(t)} + b\right)$$
$$\hat{\mathbf{x}}^{(t+1)} = W_o \mathbf{h}^{(t+1)}$$

This is essentially a Graph GRU: the network structure A^(t) gates how
information flows, and the hidden state accumulates belief momentum.

For interpretability, the **velocity model** is more transparent:

$$\Delta x_i^{(t)} = \sum_{j \in \mathcal{N}(i)} w_{ij}^{(t)}
\left(x_j^{(t)} - x_i^{(t)}\right) + \eta_i^{(t)}$$

This is a **graph opinion dynamics** model: each construct is pulled toward
its neighbors, weighted by edge strength, with noise η. The equilibrium
of this system (Δx = 0) is the solution to Lx = 0, i.e., the null space
of the Laplacian — the global consensus state.

### 5.2 Substantive Interpretation

The temporal model does three things:

**Forecasting**: given the network at wave 7, predict the belief state
at wave 8. The residual — actual minus predicted — is the **unexplained
shock**: belief changes that cannot be accounted for by network dynamics
alone. Large residuals identify constructs that changed for exogenous
reasons (political events, economic crises, generational turnover).

**Counterfactual analysis**: what would the belief state at wave 7 have
been if the network structure had remained as in wave 5? This separates
structural change (the network rewired) from dynamic change (beliefs moved
along a fixed network).

**Equilibrium analysis**: what belief state is the network at wave t
"pulling toward"? The velocity model has a fixed point; the distance of
the actual belief state from this fixed point measures how far the society
is from its network-implied equilibrium. A society far from equilibrium is
in a transitional state; one near equilibrium has stable, self-consistent
beliefs.

### 5.3 Pitfalls

**You have few time points.** WVS has 7 waves (roughly 1981–2022). Fitting
a graph RNN with fewer than 10 time points per country is statistically
underpowered. Use the temporal model for forecasting and residual analysis
rather than parameter estimation. Or pool across countries (treating each
country-wave as one observation) to gain statistical power at the cost of
assuming cross-national homogeneity.

**The network changes between waves.** W^(t) is itself estimated from
data at each wave. The temporal model then has **estimated regressors**
on the right-hand side — a standard errors-in-variables problem. The
network measurement error propagates into the dynamic estimates. Bootstrap
or propagate uncertainty from the network estimation step.

**Belief states are aggregate means, not individual trajectories.** Your
x^(t) is the country-level mean response at each wave — not an individual
panel. You're modeling population-level dynamics, not individual belief
change. The graph RNN is then a **macro-level** model. Individual-level
dynamics (persuasion, social influence) are aggregated away.

**Equilibrium may not be unique.** The velocity model has a unique
equilibrium if L is positive definite (connected graph). If the graph has
multiple components, each component converges to its own consensus. More
complex nonlinear dynamics can have multiple equilibria — the belief system
can be "attracted" to different stable configurations depending on initial
conditions. This is ideologically significant: it means the same network
structure can sustain multiple stable belief systems.

### 5.4 Python Implementation

```python
import numpy as np
from scipy.linalg import null_space
from typing import Dict, List, Optional, Tuple


class TemporalBeliefDynamics:
    """
    Temporal dynamics model for WVS belief networks across waves.
    """

    def __init__(
        self,
        wave_weights: Dict[int, np.ndarray],   # wave → W matrix (k×k)
        wave_beliefs: Dict[int, np.ndarray],   # wave → x vector (k,) mean responses
        construct_labels: List[str]
    ):
        self.W      = wave_weights
        self.x      = wave_beliefs
        self.labels = construct_labels
        self.k      = next(iter(wave_beliefs.values())).shape[0]
        self.waves  = sorted(wave_weights.keys())

    def _row_normalize(self, W: np.ndarray) -> np.ndarray:
        rs = np.abs(W).sum(axis=1, keepdims=True)
        rs[rs == 0] = 1.0
        return np.abs(W) / rs

    def graph_autoregression_predict(
        self,
        wave_t: int,
        activation: str = 'linear'
    ) -> np.ndarray:
        """
        One-step prediction: x̂(t+1) = f(A(t) x(t))
        Returns predicted belief vector for wave_t + 1.
        """
        A   = self._row_normalize(self.W[wave_t])
        x_t = self.x[wave_t]
        z   = A @ x_t

        if activation == 'linear':
            return z
        elif activation == 'tanh':
            return np.tanh(z)
        elif activation == 'relu':
            return np.maximum(z, 0)
        else:
            raise ValueError(f"Unknown activation: {activation}")

    def compute_residuals(self) -> pd.DataFrame:
        """
        For each consecutive wave pair, compute prediction residuals.
        Identifies constructs with unexplained belief shifts.
        """
        import pandas as pd
        rows = []
        for i in range(len(self.waves) - 1):
            t   = self.waves[i]
            t1  = self.waves[i + 1]
            if t1 not in self.x:
                continue
            x_pred = self.graph_autoregression_predict(t)
            x_true = self.x[t1]
            resid  = x_true - x_pred

            for j, label in enumerate(self.labels):
                rows.append({
                    'wave_from':   t,
                    'wave_to':     t1,
                    'construct':   label,
                    'x_predicted': float(x_pred[j]),
                    'x_actual':    float(x_true[j]),
                    'residual':    float(resid[j]),
                    'abs_residual': float(abs(resid[j])),
                })

        df = pd.DataFrame(rows)
        return df

    def equilibrium_state(self, wave: int) -> np.ndarray:
        """
        Compute the network-implied equilibrium belief state.
        This is the null space of L = D - A, i.e., the constant vector
        (all constructs at consensus) for a connected graph.
        For disconnected graphs: each component reaches its own consensus.
        """
        W_sym = (np.abs(self.W[wave]) + np.abs(self.W[wave]).T) / 2
        deg   = W_sym.sum(axis=1)
        L     = np.diag(deg) - W_sym
        ns    = null_space(L)
        # For connected graph: null space is the all-ones vector
        # Equilibrium value = weighted mean of initial belief state
        x_t    = self.x[wave]
        eq     = np.full(self.k, np.dot(deg, x_t) / deg.sum())
        return eq

    def distance_from_equilibrium(self) -> Dict[int, float]:
        """
        For each wave, compute distance of actual belief state from equilibrium.
        Large distance = transitional society; small = stable.
        """
        return {
            wave: float(np.linalg.norm(self.x[wave] - self.equilibrium_state(wave)))
            for wave in self.waves
            if wave in self.x
        }

    def velocity_field(self, wave: int) -> np.ndarray:
        """
        Compute the velocity vector Δx_i = Σ_j w_ij (x_j - x_i) for each construct.
        Positive = construct being pulled upward by its neighbors.
        Negative = construct being pulled downward.
        """
        W   = self.W[wave]
        x   = self.x[wave]
        vel = np.zeros(self.k)
        for i in range(self.k):
            for j in range(self.k):
                if W[i, j] != 0:
                    vel[i] += W[i, j] * (x[j] - x[i])
        return vel

    def forecast(
        self,
        from_wave: int,
        n_steps: int,
        noise_scale: float = 0.0
    ) -> np.ndarray:
        """
        Multi-step forecast from a given wave.
        Returns (n_steps+1, k) array of belief trajectories.
        Uses the last available network if wave not found.
        """
        trajectory = np.zeros((n_steps + 1, self.k))
        trajectory[0] = self.x[from_wave]

        available_waves = sorted(self.W.keys())
        last_wave = available_waves[-1]

        for step in range(n_steps):
            # Use most recent available network
            w = min(available_waves, key=lambda w: abs(w - (from_wave + step)))
            A = self._row_normalize(self.W[w])
            x_t = trajectory[step]
            trajectory[step + 1] = A @ x_t
            if noise_scale > 0:
                trajectory[step + 1] += np.random.randn(self.k) * noise_scale

        return trajectory
```

---

## Stage 6: Curvature-Weighted Opinion Dynamics

### 6.1 Mathematical Motivation

The previous stages treat all edges as passive conduits. But the Ricci
curvature κ(i,j) of each edge encodes its **geometric role** in the network:

- **κ(i,j) > 0** (positive curvature): the neighborhoods of i and j overlap
  substantially. This edge is embedded in a locally sphere-like region —
  a densely connected clique where information circulates within a community.
  Positive curvature edges are **belief reinforcement** channels: they
  amplify existing consensus within a community.

- **κ(i,j) < 0** (negative curvature): the neighborhoods of i and j are
  sparse and divergent. This edge is a bridge or bottleneck — a hyperbolic
  region where information passes between communities. Negative curvature
  edges are **belief transmission** channels: they spread information but
  attenuate it.

- **κ(i,j) ≈ 0** (flat): this edge is in a tree-like region. Belief
  propagates along it without local reinforcement.

The **curvature-weighted opinion dynamics** model modifies the velocity
field to account for this geometry:

$$\frac{dx_i}{dt} = \sum_{j \in \mathcal{N}(i)} w_{ij}\, (1 + \kappa_{ij})
\cdot (x_j - x_i)$$

Positive curvature amplifies the pull (reinforcement), negative curvature
dampens it (transmission loss across bridges). The factor (1 + κ) acts as
a **geometric weighting** of the influence.

On the gamma surface, this corresponds to flowing along geodesics weighted
by curvature. The curvature-modified Laplacian:

$$L^\kappa_{ij} = \begin{cases}
-w_{ij}(1 + \kappa_{ij}) & i \neq j, (i,j) \in E \\
\sum_{j'} w_{ij'}(1 + \kappa_{ij'}) & i = j
\end{cases}$$

governs the dynamics. Its eigenstructure reveals the **curvature-modified
diffusion modes** — how beliefs spread on the curved gamma surface rather
than on the flat approximation.

### 6.2 Substantive Interpretation

The curvature-weighted model adds interpretive depth that the flat models miss:

**Belief reinforcement bubbles**: clusters of constructs connected by
positive-curvature edges form self-reinforcing ideological chambers. Belief
perturbations within these clusters amplify and stabilize quickly. These
are the constructs that, once shifted together, lock in — e.g., a cluster
of nationalist beliefs that reinforce each other.

**Belief transmission bottlenecks**: edges with strongly negative curvature
are the bridges between ideological communities. A belief shift in one
community propagates to another only through these bottleneck edges, and
it does so at attenuated strength. Identifying these edges tells you where
the fragile connections between ideological worlds are.

**Curvature surgery**: if you remove negative-curvature edges (the bridges),
what happens? The network fragments into ideologically separate communities.
This is the topological signature of **polarization** — a society where
ideological communities have retreated from each other, leaving only weak
bridges. The rate of curvature change across waves (is κ becoming more
negative on bridging edges?) is a **curvature-based polarization index**.

**Ricci flow on belief networks**: the continuous analog is the Ricci
flow — the curvature is evolved over time to smooth the manifold. Applied
to belief networks, Ricci flow would identify the "most natural"
homogenization of the belief structure — what the network would look like
if curvature were uniform. The distance from the actual network to the
Ricci-flattened network is a measure of ideological tension.

### 6.3 Pitfalls

**Ricci curvature is expensive and approximate.** The Ollivier-Ricci
curvature uses the Wasserstein distance between neighborhoods, computed
via optimal transport. The Sinkhorn approximation in the Julia code
introduces regularization bias. For high-precision curvature, use exact
OT solvers (slower) or the Forman-Ricci curvature (exact but less
geometrically faithful):

$$\text{Forman}(e_{ij}) = w_{ij}\!\left(\frac{w_i + w_j}{w_{ij}}
- \sum_{e_k \sim e_{ij}} \frac{w_{ij}}{\sqrt{w_{ij} w_k}}\right)$$

where the sum is over edges adjacent to e_{ij}. Forman curvature is
exact, fast, and computable in Python without OT.

**Curvature depends on edge weight definition.** The geometric meaning of
κ depends on your distance metric. If you use 1 - |w| as distance (as
in the pipeline), high-weight edges are short (close constructs). Curvature
then reflects the local geometry in weight-space. If you use a different
metric, curvature changes. Always interpret curvature relative to the
metric you've defined.

**The (1 + κ) weighting can produce negative weights.** If κ < -1 for some
edge, the effective weight becomes negative — the edge repels rather than
attracts. This is mathematically valid (it models anti-alignment) but
requires careful interpretation: it means the two constructs actively
diverge in the opinion dynamics, pulled apart by the geometry of the space.

### 6.4 Python Implementation

```python
import numpy as np
from typing import Dict, List, Optional, Tuple


class CurvatureWeightedDynamics:
    """
    Opinion dynamics on the belief manifold, weighted by Ricci curvature.
    """

    def __init__(
        self,
        W: np.ndarray,
        ricci: np.ndarray,
        construct_labels: List[str],
        dt: float = 0.01,
    ):
        """
        Parameters
        ----------
        W : (k,k) weight matrix (symmetrized)
        ricci : (k,k) Ollivier-Ricci curvature matrix
        dt : integration time step
        """
        W_sym = (np.abs(W) + np.abs(W).T) / 2
        np.fill_diagonal(W_sym, 0)
        self.W      = W_sym
        self.kappa  = ricci
        self.labels = construct_labels
        self.k      = W_sym.shape[0]
        self.dt     = dt

        # Curvature-modified adjacency
        self.W_kappa = W_sym * (1.0 + ricci)
        self.W_kappa = np.maximum(self.W_kappa, 0)  # clip negatives optionally
        np.fill_diagonal(self.W_kappa, 0)

        # Curvature-modified Laplacian
        deg_k = self.W_kappa.sum(axis=1)
        self.L_kappa = np.diag(deg_k) - self.W_kappa

        # Eigendecomposition for fast integration
        from scipy.linalg import eigh
        self.eigenvalues_k, self.eigenvectors_k = eigh(self.L_kappa)
        self.eigenvalues_k = np.maximum(self.eigenvalues_k, 0)

    @staticmethod
    def forman_ricci(W: np.ndarray) -> np.ndarray:
        """
        Exact Forman-Ricci curvature (fast alternative to Ollivier).
        Does not require OT computation.
        """
        n = W.shape[0]
        kappa = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if W[i,j] == 0:
                    continue
                w_ij = W[i, j]
                # Node weights = sum of adjacent edge weights
                w_i = W[i].sum() - w_ij
                w_j = W[j].sum() - w_ij

                # Parallel edges: edges sharing one endpoint with (i,j)
                parallel_sum = 0.0
                for k in range(n):
                    if k == i or k == j:
                        continue
                    if W[i, k] > 0:
                        parallel_sum += w_ij / np.sqrt(w_ij * W[i, k])
                    if W[j, k] > 0:
                        parallel_sum += w_ij / np.sqrt(w_ij * W[j, k])

                kappa[i, j] = w_ij * (
                    (w_i + w_j) / w_ij - parallel_sum
                )
        return kappa

    def velocity(self, x: np.ndarray) -> np.ndarray:
        """
        Compute curvature-weighted velocity field at belief state x.
        Δx_i = Σ_j w_ij (1 + κ_ij)(x_j - x_i)
        """
        return -self.L_kappa @ x

    def integrate(
        self,
        x0: np.ndarray,
        n_steps: int,
        method: str = 'spectral'
    ) -> np.ndarray:
        """
        Integrate dynamics from initial state x0.
        method: 'euler' (simple), 'spectral' (exact for linear dynamics)
        Returns (n_steps+1, k) trajectory.
        """
        trajectory = np.zeros((n_steps + 1, self.k))
        trajectory[0] = x0

        if method == 'spectral':
            # Exact solution via eigendecomposition
            t_values = np.arange(n_steps + 1) * self.dt
            for step, t in enumerate(t_values):
                decay = np.exp(-self.eigenvalues_k * t)
                trajectory[step] = (
                    self.eigenvectors_k
                    * decay[None, :]
                ) @ (self.eigenvectors_k.T @ x0)

        elif method == 'euler':
            for step in range(n_steps):
                trajectory[step+1] = (
                    trajectory[step]
                    + self.dt * self.velocity(trajectory[step])
                )

        return trajectory

    def polarization_index(self) -> Dict:
        """
        Compute curvature-based polarization metrics.
        More negative mean edge curvature = more polarized belief network.
        """
        kappa_edges = self.kappa[self.W > 0]
        return {
            'mean_curvature':   float(kappa_edges.mean()),
            'min_curvature':    float(kappa_edges.min()),
            'std_curvature':    float(kappa_edges.std()),
            'pct_negative':     float((kappa_edges < 0).mean()),
            'pct_positive':     float((kappa_edges > 0).mean()),
            'curvature_range':  float(kappa_edges.max() - kappa_edges.min()),
        }

    def bottleneck_edges(self, top_n: int = 10) -> List[Dict]:
        """
        Identify edges with most negative Ricci curvature —
        the structural bottlenecks of belief transmission.
        """
        edges = []
        for i in range(self.k):
            for j in range(i+1, self.k):
                if self.W[i, j] > 0:
                    edges.append({
                        'i': i, 'j': j,
                        'construct_i': self.labels[i],
                        'construct_j': self.labels[j],
                        'weight':    float(self.W[i, j]),
                        'curvature': float(self.kappa[i, j]),
                        'role': 'bridge' if self.kappa[i,j] < 0 else 'reinforcer'
                    })
        return sorted(edges, key=lambda e: e['curvature'])[:top_n]

    def curvature_evolution(
        self,
        wave_weights: Dict[int, np.ndarray],
        wave_ricci:   Dict[int, np.ndarray],
    ) -> 'pd.DataFrame':
        """
        Track curvature statistics across waves — polarization trend.
        """
        import pandas as pd
        rows = []
        for wave in sorted(wave_weights.keys()):
            if wave not in wave_ricci:
                continue
            W_w = wave_weights[wave]
            k_w = wave_ricci[wave]
            edges = k_w[np.abs(W_w) > 0]
            rows.append({
                'wave':          wave,
                'mean_curvature': float(edges.mean()),
                'min_curvature':  float(edges.min()),
                'pct_negative':   float((edges < 0).mean()),
                'n_edges':        int((np.abs(W_w) > 0).sum() // 2),
            })
        return pd.DataFrame(rows)


# ── Unified scenario runner ───────────────────────────────────────────────────

def run_full_scenario(
    W: np.ndarray,
    ricci: np.ndarray,
    construct_labels: List[str],
    evidence_construct: int,
    evidence_state: int = 4,        # strongly agree
    n_states: int = 5,
    diffusion_times: Optional[List[float]] = None,
    alpha_ppr: float = 0.20,
) -> Dict:
    """
    Run all six stages for a single country network and evidence scenario.
    Returns consolidated results.
    """
    if diffusion_times is None:
        diffusion_times = [0.1, 0.5, 1.0, 5.0, 10.0]

    k = W.shape[0]

    # Stage 1: Belief Propagation
    priors = np.ones((k, n_states)) / n_states
    bp     = BeliefPropagator(W, priors, potential_type='potts', beta=2.0)
    obs    = np.zeros(n_states); obs[evidence_state] = 1.0
    bp_result = bp.propagate_scenario(
        evidence_construct, evidence_state, construct_labels
    )

    # Stage 2: Spectral Diffusion
    sd = SpectralDiffusion(W, normalized=True)
    x0 = np.zeros(k); x0[evidence_construct] = 1.0
    diffusion_trajectories = {
        t: sd.diffuse(x0, t) for t in diffusion_times
    }
    fiedler = sd.fiedler_analysis(construct_labels)

    # Stage 3: PPR Influence
    ppr    = PPRInfluenceMapper(W, alpha=alpha_ppr)
    ppr_Pi = ppr.full_ppr_matrix()
    ppr_result = ppr.analyze(construct_labels)
    shift_result = ppr.influence_of_shift(
        evidence_construct, 1.0, ppr_Pi, construct_labels
    )

    # Stage 6: Curvature Dynamics
    cwd = CurvatureWeightedDynamics(W, ricci, construct_labels)
    traj = cwd.integrate(x0, n_steps=200, method='spectral')
    bottlenecks   = cwd.bottleneck_edges(top_n=10)
    polarization  = cwd.polarization_index()

    return {
        'belief_propagation':     bp_result,
        'spectral_diffusion':     {'fiedler': fiedler,
                                   'trajectories': diffusion_trajectories},
        'ppr_influence':          {**ppr_result, 'shift': shift_result},
        'curvature_dynamics':     {'trajectory': traj,
                                   'bottlenecks': bottlenecks,
                                   'polarization': polarization},
    }
```

---

## Summary: Methodological Decision Tree

```
What do you want to know?
│
├── "Given this belief, what else follows?" (single country)
│         └── Stage 1: Belief Propagation
│
├── "At what scale do beliefs spread?" (single country)
│         └── Stage 2: Spectral Diffusion + scale sweep
│
├── "Which construct has widest influence?" (single country)
│         └── Stage 3: Personalized PageRank
│
├── "How does a shift in country A affect country B?"
│         └── Stage 4: Multilayer Message Passing
│
├── "What does the network predict for the next wave?"
│         └── Stage 5: Temporal Dynamics
│
└── "Where do beliefs amplify vs. attenuate? Is society polarizing?"
          └── Stage 6: Curvature-Weighted Dynamics
```

---

## Pitfall Summary Table

| Pitfall | Affects | Mitigation |
|---|---|---|
| Loopy BP may not converge | Stage 1 | Damping + iteration cap; treat as soft evidence |
| Gaussian potential distorts ordinal data | Stage 1 | Use Potts model for Likert scales |
| Directed edges break standard BP | Stage 1 | Symmetrize or use directed graphical model |
| Diffusion time t is arbitrary | Stage 2 | Sweep t; use diffusion distance as TDA input |
| Disconnected components break diffusion | Stage 2 | Run per component; check β₀ from TDA first |
| PPR conflates reach with proximity | Stage 3 | Compare hub scores across α values |
| Influence ≠ causation | Stage 3, 4 | Frame as structural influence; add causal layer separately |
| GW transport plan is approximate | Stage 4 | Report transport uncertainty; threshold at mass > 1/k |
| Dense supra-graph is intractable | Stage 4 | Use sparse nearest-neighbor country graph |
| Few time points for temporal model | Stage 5 | Pool across countries; report forecast intervals |
| Estimated regressors in temporal model | Stage 5 | Bootstrap network estimation + dynamics jointly |
| Ricci curvature is expensive | Stage 6 | Use Forman-Ricci as fast exact alternative |
| (1+κ) can produce negative weights | Stage 6 | Clip to zero or interpret repulsion explicitly |
| All models assume linearity | 2, 5, 6 | Add nonlinear terms for large shocks; use neural variants |

---

## Dependencies

```bash
pip install numpy pandas scipy networkx matplotlib seaborn scikit-learn
pip install ripser persim giotto-tda POT
# Julia: see setup.jl for Floyd-Warshall and Ricci acceleration
```
