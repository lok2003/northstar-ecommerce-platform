import { useEffect, useMemo, useState } from "react";
import "./App.css";

const CART_ID_KEY = "northstar-cart-id";
const TOKEN_KEY = "northstar-token";

function getCartId() {
  const saved = localStorage.getItem(CART_ID_KEY);
  if (saved) return saved;

  const id =
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (character) => {
          const random = Math.floor(Math.random() * 16);
          return (character === "x" ? random : (random & 3) | 8).toString(16);
        });
  localStorage.setItem(CART_ID_KEY, id);
  return id;
}

const cartId = getCartId();
const money = (cents) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);

async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Cart-Id": cartId,
      ...options.headers,
    },
  });
  if (response.status === 204) return null;

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "The request could not be completed.");
  }
  return data;
}

export default function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [category, setCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState(null);

  async function refreshCart() {
    const data = await request("/cart");
    setCart(data.items);
  }

  useEffect(() => {
    Promise.all([request("/products"), request("/cart")])
      .then(([productData, cartData]) => {
        setProducts(productData);
        setCart(cartData.items);
      })
      .catch((error) => setNotice({ type: "error", text: error.message }))
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(
    () => ["All", ...new Set(products.map((product) => product.category))],
    [products],
  );
  const visibleProducts = useMemo(
    () =>
      products.filter((product) => {
        const matchesCategory =
          category === "All" || product.category === category;
        const matchesSearch = `${product.name} ${product.description}`
          .toLowerCase()
          .includes(search.toLowerCase());
        return matchesCategory && matchesSearch;
      }),
    [category, products, search],
  );
  const cartItems = useMemo(
    () =>
      cart
        .map((item) => {
          const product = products.find((entry) => entry.id === item.product_id);
          return product ? { ...product, quantity: item.quantity } : null;
        })
        .filter(Boolean),
    [cart, products],
  );
  const cartCount = cart.reduce((total, item) => total + item.quantity, 0);
  const cartTotal = cartItems.reduce(
    (total, item) => total + item.price_cents * item.quantity,
    0,
  );

  async function changeQuantity(productId, quantity) {
    setBusy(true);
    try {
      if (quantity < 1) {
        await request(`/cart/items/${productId}`, { method: "DELETE" });
      } else {
        await request(`/cart/items/${productId}`, {
          method: "PUT",
          body: JSON.stringify({ product_id: productId, quantity }),
        });
      }
      await refreshCart();
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    } finally {
      setBusy(false);
    }
  }

  async function addToCart(product) {
    setBusy(true);
    setNotice(null);
    try {
      await request("/cart/items", {
        method: "POST",
        body: JSON.stringify({ product_id: product.id, quantity: 1 }),
      });
      await refreshCart();
      setNotice({ type: "success", text: `${product.name} added to your bag.` });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    } finally {
      setBusy(false);
    }
  }

  async function authenticate(event) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      if (mode === "register") {
        await request("/auth/register", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        setMode("login");
        setNotice({ type: "success", text: "Account created. Sign in to continue." });
        return;
      }
      const data = await request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      localStorage.setItem(TOKEN_KEY, data.token);
      setToken(data.token);
      setAuthOpen(false);
      setPassword("");
      setNotice({ type: "success", text: `Welcome back, ${username}.` });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    } finally {
      setBusy(false);
    }
  }

  async function checkout() {
    if (!token) {
      setCartOpen(false);
      setMode("login");
      setAuthOpen(true);
      setNotice({ type: "error", text: "Sign in to place your order." });
      return;
    }
    setBusy(true);
    setNotice(null);
    try {
      const order = await request("/checkout", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: "{}",
      });
      await refreshCart();
      setCartOpen(false);
      setNotice({
        type: "success",
        text: `Order ${order.order_id.slice(0, 8)} placed. Demo payment approved for ${money(order.total_cents)}.`,
      });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    } finally {
      setBusy(false);
    }
  }

  function signOut() {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setNotice({ type: "success", text: "You have signed out." });
  }

  return (
    <main>
      <div className="announcement">
        <span>Complimentary shipping on orders over $100</span>
        <span className="announcement-note">Thoughtfully made. Ready for anywhere.</span>
      </div>
      <header className="site-header">
        <a className="wordmark" href="#" aria-label="Northstar home">
          northstar<span>®</span>
        </a>
        <nav className="main-nav" aria-label="Shop categories">
          <a href="#shop">Shop all</a>
          <a href="#shop" onClick={() => setCategory("Clothing")}>Apparel</a>
          <a href="#shop" onClick={() => setCategory("Accessories")}>Accessories</a>
        </nav>
        <div className="header-actions">
          {token ? (
            <button className="account-link" onClick={signOut}>Sign out</button>
          ) : (
            <button className="account-link" onClick={() => { setMode("login"); setAuthOpen(true); }}>
              Sign in
            </button>
          )}
          <button className="bag-button" onClick={() => setCartOpen(true)} aria-label={`Open bag, ${cartCount} items`}>
            Bag <span>{cartCount}</span>
          </button>
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">GO A LITTLE FURTHER</p>
          <h1>Made for the<br /><em>in-between.</em></h1>
          <p className="hero-description">
            Considered essentials for early starts, long weekends, and everything
            that happens along the way.
          </p>
          <a className="dark-button hero-button" href="#shop">Explore the collection <span>↗</span></a>
        </div>
        <div className="hero-art" aria-label="Illustration of the outdoors">
          <div className="sun"></div>
          <div className="mountain mountain-back"></div>
          <div className="mountain mountain-front"></div>
          <div className="hero-art-caption"><span>FIELD NOTES / 01</span><span>THE OPEN ROAD</span></div>
        </div>
        <div className="hero-index"><span>01</span><i></i><span>03</span></div>
      </section>

      <section className="shop-section" id="shop">
        <div className="section-heading">
          <div>
            <p className="eyebrow">THE EVERYDAY EDIT</p>
            <h2>Good things, built to go.</h2>
          </div>
          <p className="section-note">A few of our current favorites.<br />Made to earn their keep.</p>
        </div>
        <div className="shop-tools">
          <div className="category-list" aria-label="Filter by category">
            {categories.map((item) => (
              <button
                key={item}
                className={category === item ? "category-chip active" : "category-chip"}
                onClick={() => setCategory(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <label className="search-box">
            <span aria-hidden="true">⌕</span>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find your next favorite" />
          </label>
        </div>

        {loading ? (
          <p className="loading-message">Gathering the good stuff...</p>
        ) : visibleProducts.length ? (
          <div className="product-grid">
            {visibleProducts.map((product, index) => (
              <article className="product-card" key={product.id}>
                <div className="product-art" style={{ backgroundColor: product.color }}>
                  {product.badge && <span className="product-badge">{product.badge}</span>}
                  <span className={`product-emoji product-emoji-${index % 4}`} aria-hidden="true">{product.icon}</span>
                  <span className="art-orbit orbit-one"></span>
                  <span className="art-orbit orbit-two"></span>
                  <button className="quick-add" onClick={() => addToCart(product)} disabled={busy} aria-label={`Add ${product.name} to bag`}>+</button>
                </div>
                <div className="product-info">
                  <div><h3>{product.name}</h3><span>{product.category}</span></div>
                  <strong>{money(product.price_cents)}</strong>
                </div>
                <p className="product-description">{product.description}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="loading-message">Nothing found. Try another search.</p>
        )}
      </section>

      <section className="story-strip">
        <span className="story-mark">N.</span>
        <p>Less noise. Better things.<br /><em>That’s the whole idea.</em></p>
        <a href="#shop">A little more about us <span>↗</span></a>
      </section>

      <footer className="site-footer">
        <a className="wordmark" href="#">northstar<span>®</span></a>
        <span>Considered goods for the road ahead.</span>
        <span>© 2025 Northstar Supply Co.</span>
      </footer>

      {notice && (
        <div className={`toast ${notice.type}`} role="status">
          <span>{notice.text}</span>
          <button onClick={() => setNotice(null)} aria-label="Dismiss notification">×</button>
        </div>
      )}

      {cartOpen && (
        <div className="overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) setCartOpen(false); }}>
          <aside className="side-panel" aria-label="Shopping bag">
            <div className="drawer-heading">
              <div><p className="eyebrow">YOUR EDIT</p><h2>Shopping bag <span>({cartCount})</span></h2></div>
              <button className="close-button" onClick={() => setCartOpen(false)} aria-label="Close bag">×</button>
            </div>
            {cartItems.length ? (
              <>
                <div className="drawer-items">
                  {cartItems.map((item) => (
                    <article className="drawer-item" key={item.id}>
                      <div className="drawer-art" style={{ backgroundColor: item.color }}>{item.icon}</div>
                      <div className="drawer-item-info">
                        <div className="drawer-item-title"><h3>{item.name}</h3><strong>{money(item.price_cents * item.quantity)}</strong></div>
                        <span>{item.category}</span>
                        <div className="quantity-control">
                          <button onClick={() => changeQuantity(item.id, item.quantity - 1)} disabled={busy} aria-label={`Remove one ${item.name}`}>−</button>
                          <span>{item.quantity}</span>
                          <button onClick={() => changeQuantity(item.id, item.quantity + 1)} disabled={busy} aria-label={`Add one ${item.name}`}>+</button>
                          <button className="remove-link" onClick={() => changeQuantity(item.id, 0)} disabled={busy}>Remove</button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
                <div className="drawer-bottom">
                  <div className="subtotal"><span>Subtotal</span><strong>{money(cartTotal)}</strong></div>
                  <p>Shipping and taxes calculated at checkout.</p>
                  <button className="dark-button checkout-button" onClick={checkout} disabled={busy}>
                    {busy ? "One moment..." : token ? "Place demo order" : "Sign in to checkout"} <span>→</span>
                  </button>
                  <span className="demo-caption">Demo checkout · no real payment will be taken</span>
                </div>
              </>
            ) : (
              <div className="empty-bag"><span>✳</span><h3>Your bag is taking a breather.</h3><p>Find something good for the road ahead.</p><button className="dark-button" onClick={() => setCartOpen(false)}>Explore the collection <span>↗</span></button></div>
            )}
          </aside>
        </div>
      )}

      {authOpen && (
        <div className="overlay auth-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) setAuthOpen(false); }}>
          <section className="auth-card" aria-label={mode === "login" ? "Sign in" : "Create account"}>
            <button className="close-button auth-close" onClick={() => setAuthOpen(false)} aria-label="Close sign in">×</button>
            <p className="eyebrow">WELCOME TO NORTHSTAR</p>
            <h2>{mode === "login" ? "Good to see you." : "Make yourself at home."}</h2>
            <p className="auth-description">Sign in to make checkout a little easier.</p>
            <form onSubmit={authenticate} className="auth-form">
              <label>Email or username<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required /></label>
              <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={8} required /></label>
              <button className="dark-button checkout-button" disabled={busy}>{busy ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"} <span>→</span></button>
            </form>
            <p className="auth-switch">
              {mode === "login" ? "New around here?" : "Already have an account?"}{" "}
              <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setNotice(null); }}>
                {mode === "login" ? "Create an account" : "Sign in"}
              </button>
            </p>
            <p className="auth-hint">Learning demo: account data is stored in memory and resets when the service restarts.</p>
          </section>
        </div>
      )}
    </main>
  );
}
