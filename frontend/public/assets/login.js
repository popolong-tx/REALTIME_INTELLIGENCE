(() => {
  'use strict';

  const form = document.getElementById('login-form');
  const username = document.getElementById('login-username');
  const password = document.getElementById('login-password');
  const message = document.getElementById('login-message');
  const submit = document.getElementById('login-submit');
  const toggle = document.getElementById('toggle-password');

  function safeNextPath() {
    const candidate = new URLSearchParams(window.location.search).get('next') || '/';
    return candidate.startsWith('/') && !candidate.startsWith('//') ? candidate : '/';
  }

  function setMessage(value) {
    message.textContent = value || '';
  }

  async function readPayload(response) {
    const type = response.headers.get('content-type') || '';
    return type.includes('application/json') ? response.json() : response.text();
  }

  toggle.addEventListener('click', () => {
    const showing = password.type === 'text';
    password.type = showing ? 'password' : 'text';
    toggle.textContent = showing ? '显示' : '隐藏';
    toggle.setAttribute('aria-label', showing ? '显示密码' : '隐藏密码');
    toggle.setAttribute('aria-pressed', String(!showing));
    password.focus();
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    setMessage('');
    if (!username.value.trim() || !password.value) {
      setMessage('请输入用户名和密码。');
      (!username.value.trim() ? username : password).focus();
      return;
    }
    submit.disabled = true;
    submit.querySelector('span').textContent = '正在验证';
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.value.trim(), password: password.value }),
      });
      const payload = await readPayload(response);
      if (!response.ok) {
        const detail = typeof payload === 'object' ? payload.detail : payload;
        throw new Error(detail || '登录失败，请稍后重试。');
      }
      window.location.replace(safeNextPath());
    } catch (error) {
      setMessage(error.message || '登录失败，请稍后重试。');
      password.value = '';
      password.focus();
    } finally {
      submit.disabled = false;
      submit.querySelector('span').textContent = '登录';
    }
  });

  fetch('/api/v1/auth/status', { headers: { Accept: 'application/json' } })
    .then(readPayload)
    .then((status) => {
      if (status.authenticated) window.location.replace(safeNextPath());
      else if (status.configured === false) setMessage('服务端尚未配置登录账号，请联系管理员。');
    })
    .catch(() => setMessage('暂时无法连接登录服务，请稍后重试。'));
})();
