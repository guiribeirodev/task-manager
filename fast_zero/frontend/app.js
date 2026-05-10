
const tokenKey = 'fast-zero-token';
let isLoading = false;

const authView = document.querySelector('#auth-view');
const appView = document.querySelector('#app-view');
const loginForm = document.querySelector('#login-form');
const registerForm = document.querySelector('#register-form');
const loginTab = document.querySelector('#login-tab');
const registerTab = document.querySelector('#register-tab');
const authMessage = document.querySelector('#auth-message');
const appMessage = document.querySelector('#app-message');

const colTodo = document.querySelector('#col-todo');
const colDoing = document.querySelector('#col-doing');
const colDone = document.querySelector('#col-done');

const summary = document.querySelector('#summary');
const todoTemplate = document.querySelector('#todo-template');
const todoForm = document.querySelector('#todo-form');
const logoutButton = document.querySelector('#logout-button');
const filterTitle = document.querySelector('#filter-title');

function token() { return localStorage.getItem(tokenKey); }

function setMessage(element, text = '', type = '') {
  element.textContent = text;
  element.classList.toggle('is-error', type === 'error');
  element.classList.toggle('is-success', type === 'success');
  if (text) {
    setTimeout(() => {
      element.textContent = '';
      element.classList.remove('is-error', 'is-success');
    }, 3000);
  }
}

function showApp(isAuthenticated) {
  if (isAuthenticated) {
    authView.classList.add('is-hidden');
    appView.classList.remove('is-hidden');
  } else {
    appView.classList.add('is-hidden');
    authView.classList.remove('is-hidden');
  }
}

async function request(path, options = {}) {
  if (isLoading && !options.skipLoading) throw new Error('Aguarde a operação atual terminar.');
  isLoading = true;
  const headers = new Headers(options.headers || {});
  if (token()) headers.set('Authorization', `Bearer ${token()}`);
  if (options.body && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  try {
    const response = await fetch(path, { ...options, headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const errorMsg = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
      throw new Error(errorMsg || 'Não foi possível concluir a operação.');
    }
    return data;
  } finally {
    isLoading = false;
  }
}

function setAuthTab(mode) {
  const isLogin = mode === 'login';
  loginTab.classList.toggle('is-active', isLogin);
  registerTab.classList.toggle('is-active', !isLogin);
  loginForm.classList.toggle('is-hidden', !isLogin);
  registerForm.classList.toggle('is-hidden', isLogin);
  setMessage(authMessage);
}

async function login(email, password) {
  const form = new URLSearchParams();
  form.set('username', email);
  form.set('password', password);
  const data = await request('/auth/token', {
    body: form, headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, method: 'POST',
  });
  localStorage.setItem(tokenKey, data.access_token);
  showApp(true);
  loginForm.reset();
  registerForm.reset();
  await Promise.all([loadUser(), loadTodos()]);
}

function todoPayload(form) {
  return { title: form.title.value.trim(), description: form.description.value.trim(), state: form.state.value };
}

function filterParams() {
  const params = new URLSearchParams();
  const title = filterTitle.value.trim();
  if (title.length >= 3) params.set('title', title);
  return params.toString();
}

async function loadTodos() {
  const query = filterParams();
  const data = await request(`/todos/${query ? `?${query}` : ''}`);
  renderTodos(data.todos || []);
}

async function loadUser() {
  try {
    const user = await request('/users/me');
    const greeting = document.querySelector('#greeting');
    if (greeting) greeting.textContent = `Bom dia, ${user.username}`;
  } catch (error) {
    console.error('Failed to load user', error);
  }
}


const stateMap = {
  draft: 'todo',
  todo: 'todo',
  doing: 'doing',
  done: 'done',
  trash: null
};

const labelMap = {
  draft: 'Rascunho', todo: 'A fazer', doing: 'Em andamento', done: 'Concluído', trash: 'Lixeira'
};

function renderTodos(todos) {
  colTodo.replaceChildren();
  colDoing.replaceChildren();
  colDone.replaceChildren();
  
  let pendingCount = 0;
  
  todos.forEach((todo) => {
    if (todo.state === 'trash') return;
    if (todo.state !== 'done') pendingCount++;
    
    const item = todoTemplate.content.firstElementChild.cloneNode(true);
    const titleInput = item.querySelector('.todo-title');
    titleInput.value = todo.title;
    titleInput.addEventListener('focus', () => titleInput.select());
    
    const descInput = item.querySelector('.todo-description');
    descInput.value = todo.description;
    descInput.addEventListener('focus', () => descInput.select());
    
    const stateSelect = item.querySelector('.todo-state');
    stateSelect.value = todo.state;
    
    const badge = item.querySelector('.badge');
    badge.textContent = labelMap[todo.state] || todo.state;
    badge.className = `badge ${todo.state}`;

    if(todo.state === 'done') {
      item.querySelector('.todo-title').style.textDecoration = 'line-through';
      item.querySelector('.todo-title').style.color = 'var(--text-secondary)';
    }

    item.querySelector('.save-button').addEventListener('click', async () => {
      await saveTodo(todo.id, {
        title: item.querySelector('.todo-title').value.trim(),
        description: item.querySelector('.todo-description').value.trim(),
        state: stateSelect.value,
      });
    });

    item.querySelector('.delete-button').addEventListener('click', async () => {
      await deleteTodo(todo.id, item);
    });

    const targetCol = stateMap[todo.state] || 'todo';
    if (targetCol === 'doing') colDoing.append(item);
    else if (targetCol === 'done') colDone.append(item);
    else colTodo.append(item);
  });
  
  summary.textContent = `Você tem ${pendingCount} tarefa${pendingCount !== 1 ? 's' : ''} pendente${pendingCount !== 1 ? 's' : ''} hoje.`;
}

async function saveTodo(id, payload) {
  try {
    await request(`/todos/${id}`, { body: JSON.stringify(payload), method: 'PATCH' });
    await loadTodos();
  } catch (error) { alert(error.message); }
}

async function deleteTodo(id, itemElement) {
  try {
    await request(`/todos/${id}`, { method: 'DELETE' });
    itemElement.remove();
    await loadTodos();
  } catch (error) { alert(error.message); }
}

loginTab.addEventListener('click', () => setAuthTab('login'));
registerTab.addEventListener('click', () => setAuthTab('register'));

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const data = new FormData(loginForm);
  try {
    setMessage(authMessage, 'Autenticando...');
    await login(data.get('email'), data.get('password'));
  } catch (error) { setMessage(authMessage, error.message, 'error'); }
});

registerForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = { username: registerForm.username.value.trim(), email: registerForm.email.value.trim(), password: registerForm.password.value };
  try {
    setMessage(authMessage, 'Criando sua conta...');
    await request('/users/', { body: JSON.stringify(payload), method: 'POST' });
    await login(payload.email, payload.password);
  } catch (error) { setMessage(authMessage, error.message, 'error'); }
});

todoForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await request('/todos/', { body: JSON.stringify(todoPayload(todoForm)), method: 'POST' });
    todoForm.reset();
    await loadTodos();
  } catch (error) { setMessage(appMessage, error.message, 'error'); }
});

logoutButton.addEventListener('click', () => {
  localStorage.removeItem(tokenKey);
  showApp(false);
});

let filterTimeout;
filterTitle.addEventListener('input', () => {
  clearTimeout(filterTimeout);
  filterTimeout = setTimeout(() => {
    loadTodos();
  }, 300);
});

if (token()) {
  showApp(true);
  Promise.all([loadUser(), loadTodos()]).catch(() => {
    localStorage.removeItem(tokenKey);
    showApp(false);
  });
}

const themeToggle = document.querySelector('#theme-toggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  });
  
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.body.classList.add('dark');
  }
}

