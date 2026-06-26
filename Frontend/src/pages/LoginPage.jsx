export default function LoginPage({ authError, health, loginBusy, loginForm, onLogin, onLoginFormChange, sessionNote }) {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="panel-head compact">
          <div>
            <p className="eyebrow">CyberShield AI</p>
            <h2>Acceso</h2>
          </div>
          <span className={`pill ${health === 'sin conexión' ? 'danger' : 'success'}`}>{health}</span>
        </div>

        <form className="auth-form" onSubmit={onLogin}>
          <label>
            <span>Usuario</span>
            <input
              autoComplete="username"
              autoFocus
              value={loginForm.username}
              onChange={(event) => onLoginFormChange({ ...loginForm, username: event.target.value })}
              placeholder="demo"
              required
            />
          </label>

          <label>
            <span>Contraseña</span>
            <input
              autoComplete="current-password"
              type="password"
              value={loginForm.password}
              onChange={(event) => onLoginFormChange({ ...loginForm, password: event.target.value })}
              placeholder="••••••••"
              required
            />
          </label>

          {authError ? <div className="alert">{authError}</div> : null}
          {sessionNote ? <div className="hint">{sessionNote}</div> : null}

          <button className="primary-button wide" disabled={loginBusy} type="submit">
            {loginBusy ? 'Iniciando sesión…' : 'Entrar'}
          </button>
        </form>
      </section>
    </main>
  )
}
