<script src="https://js.stripe.com/v3/"></script>
<script>
  const yearEl = document.getElementById('year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
//cart in memory
  const cart = [];
  const cartUI = document.getElementById('cart-ui');

  function renderCart() {
    if (!cartUI) return;
    cartUI.innerHTML = '';
    if (cart.length === 0) {
      cartUI.innerHTML = '<div class="micro">Cart is empty.</div>';
      return;
    }
    cart.forEach(i => {
      const d = document.createElement('div');
      d.className = 'cart-item';
      d.innerHTML = `<span class="badge">${i.sku}</span> × ${i.quantity} — <strong>$${(11.99 * i.quantity).toFixed(2)}</strong>`;
      cartUI.appendChild(d);
    });
  }

  const add = document.getElementById('add');
  if (add) {
    add.addEventListener('click', (e) => {
      e.preventDefault(); // <<< THIS STOPS THE FORM FROM RELOADING
      const flavour = document.getElementById('flavour').value;
      const qty = parseInt(document.getElementById('qty').value || '1', 10);
      cart.push({ sku: flavour, quantity: qty });
      renderCart();
    });
  }
  renderCart();