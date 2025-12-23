/**
 * ETL Dashboard V2 - Main Application
 */
import './styles/main.css';
import { api } from './services/api';
import { ws } from './services/websocket';
import type { ConfiguracaoETL, LogEntry, StatusUpdate } from './types';

// State
let config: ConfiguracaoETL | null = null;
let isExecuting = false;
let logs: LogEntry[] = [];

// DOM Elements
const app = document.getElementById('app')!;

// Option mappings
const optionIcons: Record<string, string> = {
  pdf: '📄', csv: '📊', excel: '📗', xlsx: '📗', xml: '📋',
  pdf_lote: '📄📄', excel_lote: '📗📗', xml_lote: '📋📋',
  ativo: '📈', passivo: '📉', base_total: '🗄️'
};

const optionLabels: Record<string, string> = {
  pdf: 'PDF', csv: 'CSV', excel: 'Excel', xlsx: 'Excel', xml: 'XML',
  pdf_lote: 'PDF Lote', excel_lote: 'Excel Lote', xml_lote: 'XML Lote',
  ativo: 'Ativo', passivo: 'Passivo', base_total: 'Base Total'
};

// Initialize
async function init(): Promise<void> {
  try {
    await loadConfig();
  } catch (error) {
    console.error('Erro ao carregar configuração:', error);
    // Cria configuração padrão vazia para permitir renderização
    config = {
      versao: '2.0',
      ultimaModificacao: new Date().toISOString(),
      periodo: { dataInicial: null, dataFinal: null, usarD1Anbima: true },
      sistemas: {}
    } as ConfiguracaoETL;
  }

  // Renderiza a interface SEMPRE, mesmo sem conexão
  render();
  setupEventListeners();

  // Tenta conectar WebSocket em background
  try {
    await connectWebSocket();
  } catch (error) {
    console.warn('WebSocket não conectado:', error);
  }

  // Mostra erro se não conseguiu carregar config do servidor
  if (Object.keys(config?.sistemas || {}).length === 0) {
    showToast('Erro ao conectar com o servidor. Verifique se o backend está rodando na porta 4001.', 'error');
  }
}

async function loadConfig(): Promise<void> {
  config = await api.getConfig();
}

async function connectWebSocket(): Promise<void> {
  try {
    await ws.connect();

    // Update connection status in UI after connecting
    updateConnectionStatus();

    ws.onLog((log) => {
      logs.unshift(log);
      if (logs.length > 100) logs.pop();
      renderLogs();
    });

    ws.onStatusUpdate((sistemaId, status) => {
      updateSistemaStatus(sistemaId, status);
    });

    // Subscribe to all systems
    if (config?.sistemas) {
      Object.keys(config.sistemas).forEach((id) => {
        ws.subscribeToSistemaStatus(id);
      });
    }
  } catch (error) {
    console.warn('WebSocket nao conectado:', error);
  }
}

function updateConnectionStatus(): void {
  const dot = document.querySelector('.connection-dot');
  const text = document.querySelector('.connection-status span:last-child');
  if (dot && text) {
    if (ws.isConnected()) {
      dot.classList.add('connected');
      text.textContent = 'Conectado';
    } else {
      dot.classList.remove('connected');
      text.textContent = 'Desconectado';
    }
  }
}

function render(): void {
  app.innerHTML = `
    <div class="container">
      <header>
        <div class="logo">
          <div class="logo-icon">📊</div>
          <div>
            <h1>ETL Dashboard <span class="version-badge">V2</span></h1>
            <small style="color: #666;">TypeScript + Java Spring Boot</small>
          </div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
          <div class="connection-status">
            <span class="connection-dot ${ws.isConnected() ? 'connected' : ''}"></span>
            <span>${ws.isConnected() ? 'Conectado' : 'Desconectado'}</span>
          </div>
          <button class="btn btn-secondary" onclick="openConfigSistemas()">⚙️ Config Sistemas</button>
          <button class="btn btn-secondary" onclick="saveConfig()">💾 Salvar</button>
        </div>
      </header>

      ${renderStats()}

      <div class="section">
        <div class="section-header">
          <span class="section-title">📅 Periodo</span>
        </div>
        ${renderPeriodo()}
      </div>

      <div class="section">
        <div class="section-header">
          <span class="section-title">⚙️ Sistemas</span>
          <div>
            <button class="btn btn-secondary" onclick="ativarTodos()">Ativar Todos</button>
            <button class="btn btn-secondary" onclick="desativarTodos()">Desativar Todos</button>
          </div>
        </div>
        <div class="systems-grid" id="systems-grid">
          ${renderSistemas()}
        </div>
      </div>

      <div class="section">
        <div class="action-bar">
          <label class="checkbox-label" style="display: flex; align-items: center; gap: 8px;">
            <input type="checkbox" id="checkbox-limpar" />
            <span>🧹 Limpar Pastas Antes</span>
          </label>
          <button class="btn btn-execute" onclick="executePipeline()" id="btn-executar" ${isExecuting ? 'disabled' : ''}>
            ${isExecuting ? '⏳ Executando...' : '🚀 EXECUTAR PIPELINE'}
          </button>
          <button class="btn btn-secondary" onclick="openCredentials()">🔑 Credenciais</button>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          <span class="section-title">📋 Logs</span>
          <button class="btn btn-secondary" onclick="clearLogs()">Limpar</button>
        </div>
        <div class="logs-container" id="logs-container">
          ${renderLogs()}
        </div>
      </div>
    </div>

    <div class="toast" id="toast">
      <span id="toast-icon">✅</span>
      <span id="toast-message">Mensagem</span>
    </div>
  `;
}

function renderStats(): string {
  if (!config?.sistemas) return '';

  const sistemas = Object.values(config.sistemas);
  const total = sistemas.length;
  const ativos = sistemas.filter((s) => s.ativo).length;

  return `
    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-number">${total}</div>
        <div class="stat-label">Total de Sistemas</div>
      </div>
      <div class="stat-card active">
        <div class="stat-number">${ativos}</div>
        <div class="stat-label">Ativos</div>
      </div>
      <div class="stat-card inactive">
        <div class="stat-number">${total - ativos}</div>
        <div class="stat-label">Inativos</div>
      </div>
    </div>
  `;
}

function renderPeriodo(): string {
  const periodo = config?.periodo;
  return `
    <div style="display: grid; grid-template-columns: 1fr 1fr auto; gap: 20px; align-items: end;">
      <div class="form-group">
        <label style="font-size: 0.85em; color: #888;">Data Inicial</label>
        <input type="date" id="data-inicial" value="${periodo?.dataInicial || ''}"
          style="padding: 12px 15px; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; background: rgba(255,255,255,0.05); color: #fff;">
      </div>
      <div class="form-group">
        <label style="font-size: 0.85em; color: #888;">Data Final</label>
        <input type="date" id="data-final" value="${periodo?.dataFinal || ''}"
          style="padding: 12px 15px; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; background: rgba(255,255,255,0.05); color: #fff;">
      </div>
      <div style="display: flex; align-items: center; gap: 10px; padding: 12px 0;">
        <input type="checkbox" id="usar-d1" ${periodo?.usarD1Anbima ? 'checked' : ''}
          style="width: 20px; height: 20px; accent-color: #00d4ff;">
        <label for="usar-d1">Usar D-1 ANBIMA</label>
      </div>
    </div>
  `;
}

function renderSistemas(): string {
  if (!config?.sistemas) return '';

  const sorted = Object.entries(config.sistemas)
    .sort((a, b) => (a[1].ordem || 99) - (b[1].ordem || 99));

  return sorted.map(([id, sys]) => {
    const opcoes = sys.opcoes || {};
    const optionsHtml = Object.entries(opcoes)
      .map(([key, val]) => `
        <label class="option-toggle ${val ? 'active' : ''}" onclick="toggleOption('${id}', '${key}')">
          <span>${optionIcons[key] || '⚙️'}</span>
          <span>${optionLabels[key] || key}</span>
        </label>
      `).join('');

    const statusClass = sys.status === 'RUNNING' ? 'running' : (sys.ativo ? 'active' : 'inactive');

    return `
      <div class="system-card ${statusClass}" id="card-${id}">
        <div class="system-header">
          <div class="system-info">
            <div class="system-icon">${sys.icone || '📦'}</div>
            <div>
              <div class="system-name">${sys.nome || id}</div>
              <div class="system-desc">${sys.descricao || ''}</div>
            </div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" ${sys.ativo ? 'checked' : ''} onchange="toggleSistema('${id}')">
            <span class="toggle-slider"></span>
          </label>
        </div>
        ${optionsHtml ? `<div class="system-options">${optionsHtml}</div>` : ''}
        <div class="system-progress">
          <div class="system-progress-bar" style="width: ${sys.progresso || 0}%"></div>
        </div>
        <div class="system-status">${sys.mensagem || (sys.ativo ? 'Pronto para executar' : 'Desativado')}</div>
      </div>
    `;
  }).join('');
}

function renderLogsContent(): string {
  if (logs.length === 0) {
    return `
      <div class="log-entry">
        <span class="log-time">--:--:--</span>
        <span class="log-level-INFO">[INFO]</span>
        <span>Dashboard V2 iniciado. Aguardando execucao...</span>
      </div>
    `;
  }

  return logs.map((log) => `
    <div class="log-entry">
      <span class="log-time">${new Date(log.timestamp).toLocaleTimeString('pt-BR')}</span>
      <span class="log-level-${log.level}">[${log.level}]</span>
      <span class="log-system">[${log.sistema}]</span>
      <span>${log.mensagem}</span>
    </div>
  `).join('');
}

function renderLogs(): string {
  const container = document.getElementById('logs-container');
  if (container) {
    container.innerHTML = renderLogsContent();
  }
  return renderLogsContent();
}

// Global functions
(window as any).toggleSistema = async (id: string) => {
  if (!config?.sistemas[id]) return;
  const newValue = !config.sistemas[id].ativo;
  config.sistemas[id].ativo = newValue;
  await api.toggleSistema(id, newValue);
  render();
};

(window as any).toggleOption = async (sistemaId: string, opcao: string) => {
  if (!config?.sistemas[sistemaId]?.opcoes) return;
  const newValue = !config.sistemas[sistemaId].opcoes![opcao];
  config.sistemas[sistemaId].opcoes![opcao] = newValue;
  await api.updateOpcao(sistemaId, opcao, newValue);
  render();
};

(window as any).ativarTodos = async () => {
  if (!config?.sistemas) return;
  for (const id of Object.keys(config.sistemas)) {
    config.sistemas[id].ativo = true;
    await api.toggleSistema(id, true);
  }
  render();
  showToast('Todos os sistemas ativados', 'success');
};

(window as any).desativarTodos = async () => {
  if (!config?.sistemas) return;
  for (const id of Object.keys(config.sistemas)) {
    config.sistemas[id].ativo = false;
    await api.toggleSistema(id, false);
  }
  render();
  showToast('Todos os sistemas desativados', 'success');
};

(window as any).saveConfig = async () => {
  if (!config) return;
  const dataInicial = (document.getElementById('data-inicial') as HTMLInputElement)?.value;
  const dataFinal = (document.getElementById('data-final') as HTMLInputElement)?.value;
  const usarD1 = (document.getElementById('usar-d1') as HTMLInputElement)?.checked;

  config.periodo = {
    dataInicial: dataInicial || null,
    dataFinal: dataFinal || null,
    usarD1Anbima: usarD1
  };

  await api.saveConfig(config);
  showToast('Configuracao salva!', 'success');
};

(window as any).executePipeline = async () => {
  if (isExecuting) return;

  const ativos = config?.sistemas ? Object.values(config.sistemas).filter((s) => s.ativo) : [];
  if (ativos.length === 0) {
    showToast('Nenhum sistema ativo', 'error');
    return;
  }

  // Verificar se deve limpar pastas
  const limparCheckbox = document.getElementById('checkbox-limpar') as HTMLInputElement;
  const limparPastas = limparCheckbox?.checked || false;

  isExecuting = true;
  render();

  try {
    const result = await api.executePipeline(limparPastas);
    if (result.success) {
      showToast(limparPastas ? 'Pipeline iniciado (com limpeza)!' : 'Pipeline iniciado!', 'success');
    } else {
      showToast('Erro: ' + result.error, 'error');
    }
  } catch (error) {
    showToast('Erro ao executar', 'error');
  }

  isExecuting = false;
  render();
};

(window as any).clearLogs = () => {
  logs = [];
  renderLogs();
};

(window as any).openConfigSistemas = () => {
  window.open('http://localhost:5003', '_blank');
};

(window as any).openCredentials = async () => {
  try {
    const credentials = await api.getCredentials();

    const renderSystemFields = (name: string, creds: any) => `
      <div class="cred-system">
        <div class="cred-header">${name}</div>
        <div class="cred-grid">
          <label>URL</label>
          <input type="text" data-system="${name.toLowerCase()}" data-field="url" value="${creds?.url || ''}" />
          <label>Usuário</label>
          <input type="text" data-system="${name.toLowerCase()}" data-field="username" value="${creds?.username || ''}" />
          <label>Senha</label>
          <input type="password" data-system="${name.toLowerCase()}" data-field="password" value="${creds?.password || ''}" />
        </div>
      </div>
    `;

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content" style="max-width: 800px; max-height: 85vh; overflow-y: auto;">
        <div class="modal-header">
          <h2>🔑 Credenciais dos Sistemas</h2>
          <button class="btn-close" onclick="this.closest('.modal').remove()">✕</button>
        </div>
        <div class="modal-body" style="padding: 0;">
          <style>
            .cred-tabs { display: flex; border-bottom: 1px solid #333; background: #1a1a2e; }
            .cred-tab { padding: 12px 20px; cursor: pointer; color: #888; border: none; background: none; }
            .cred-tab:hover, .cred-tab.active { color: #fff; border-bottom: 2px solid #8b5cf6; }
            .cred-panel { display: none; padding: 20px; }
            .cred-panel.active { display: block; }
            .cred-system { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
            .cred-header { font-size: 14px; font-weight: 600; color: #8b5cf6; margin-bottom: 12px; }
            .cred-grid { display: grid; grid-template-columns: 100px 1fr; gap: 8px; align-items: center; }
            .cred-grid label { color: #888; font-size: 12px; }
            .cred-grid input { background: #0f0f23; border: 1px solid #333; border-radius: 6px; padding: 8px 12px; color: #fff; font-size: 13px; }
            .cred-grid input:focus { border-color: #8b5cf6; outline: none; }
            .paths-grid { display: grid; grid-template-columns: 120px 1fr; gap: 8px; align-items: center; }
            .paths-grid label { color: #888; font-size: 11px; }
            .paths-grid input { background: #0f0f23; border: 1px solid #333; border-radius: 4px; padding: 6px 10px; color: #fff; font-size: 11px; }
          </style>
          <div class="cred-tabs">
            <button class="cred-tab active" onclick="switchCredTab(this, 'sistemas')">📊 Sistemas</button>
            <button class="cred-tab" onclick="switchCredTab(this, 'fundos')">🏢 Fundos</button>
            <button class="cred-tab" onclick="switchCredTab(this, 'paths')">📁 Pastas</button>
            <button class="cred-tab" onclick="switchCredTab(this, 'json')">📝 JSON</button>
          </div>
          <div class="cred-panel active" id="panel-sistemas">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
              ${renderSystemFields('AMPLIS REAG', credentials?.amplis?.reag)}
              ${renderSystemFields('AMPLIS MASTER', credentials?.amplis?.master)}
              ${renderSystemFields('MAPS', credentials?.maps)}
              ${renderSystemFields('FIDC', credentials?.fidc)}
              ${renderSystemFields('JCOT', credentials?.jcot)}
              ${renderSystemFields('BRITECH', credentials?.britech)}
              ${renderSystemFields('QORE', credentials?.qore)}
            </div>
          </div>
          <div class="cred-panel" id="panel-fundos">
            <style>
              .fundos-section { margin-bottom: 20px; }
              .fundos-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
              .fundos-title { font-size: 16px; font-weight: 600; color: #8b5cf6; }
              .fundos-toggle { display: flex; align-items: center; gap: 8px; }
              .fundos-toggle label { color: #888; font-size: 12px; }
              .fundos-list { max-height: 200px; overflow-y: auto; background: #0f0f23; border-radius: 8px; padding: 12px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
              .fundos-list.disabled { opacity: 0.5; pointer-events: none; }
              .fundo-item { display: flex; align-items: center; gap: 6px; }
              .fundo-item input { accent-color: #8b5cf6; }
              .fundo-item label { color: #ccc; font-size: 11px; cursor: pointer; }
            </style>
            <div class="fundos-section">
              <div class="fundos-header">
                <span class="fundos-title">FIDC - Fundos</span>
                <div class="fundos-toggle">
                  <label>Usar todos:</label>
                  <input type="checkbox" id="fidc-usar-todos" ${credentials?.fidc?.usar_todos !== false ? 'checked' : ''} onchange="toggleFundosList('fidc')" />
                </div>
              </div>
              <div class="fundos-list ${credentials?.fidc?.usar_todos !== false ? 'disabled' : ''}" id="fidc-fundos-list">
                ${(credentials?.fidc?.fundos || []).map((f: string, i: number) => `
                  <div class="fundo-item">
                    <input type="checkbox" id="fidc-fundo-${i}" data-fundos="fidc" value="${f}" ${(credentials?.fidc?.fundos_selecionados || []).includes(f) ? 'checked' : ''} />
                    <label for="fidc-fundo-${i}">${f}</label>
                  </div>
                `).join('')}
              </div>
            </div>
            <div class="fundos-section">
              <div class="fundos-header">
                <span class="fundos-title">MAPS - Fundos</span>
                <div class="fundos-toggle">
                  <label>Usar todos:</label>
                  <input type="checkbox" id="maps-usar-todos" ${credentials?.maps?.usar_todos !== false ? 'checked' : ''} onchange="toggleFundosList('maps')" />
                </div>
              </div>
              <div class="fundos-list ${credentials?.maps?.usar_todos !== false ? 'disabled' : ''}" id="maps-fundos-list">
                ${(credentials?.maps?.fundos || []).map((f: string, i: number) => `
                  <div class="fundo-item">
                    <input type="checkbox" id="maps-fundo-${i}" data-fundos="maps" value="${f}" ${(credentials?.maps?.fundos_selecionados || []).includes(f) ? 'checked' : ''} />
                    <label for="maps-fundo-${i}">${f}</label>
                  </div>
                `).join('')}
              </div>
            </div>
            <div class="fundos-section">
              <div class="fundos-header">
                <span class="fundos-title">QORE - Fundos</span>
                <div class="fundos-toggle">
                  <label>Usar todos:</label>
                  <input type="checkbox" id="qore-usar-todos" ${credentials?.qore?.usar_todos !== false ? 'checked' : ''} onchange="toggleFundosList('qore')" />
                </div>
              </div>
              <div class="fundos-list ${credentials?.qore?.usar_todos !== false ? 'disabled' : ''}" id="qore-fundos-list">
                ${(credentials?.qore?.fundos || []).map((f: string, i: number) => `
                  <div class="fundo-item">
                    <input type="checkbox" id="qore-fundo-${i}" data-fundos="qore" value="${f}" ${(credentials?.qore?.fundos_selecionados || []).includes(f) ? 'checked' : ''} />
                    <label for="qore-fundo-${i}">${f}</label>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
          <div class="cred-panel" id="panel-paths">
            <div class="cred-system">
              <div class="cred-header">📁 Caminhos de Download</div>
              <div class="paths-grid">
                <label>CSV AMPLIS</label><input type="text" data-path="csv" value="${credentials?.paths?.csv || ''}" />
                <label>PDF</label><input type="text" data-path="pdf" value="${credentials?.paths?.pdf || ''}" />
                <label>JCOT</label><input type="text" data-path="jcot" value="${credentials?.paths?.jcot || ''}" />
                <label>BRITECH</label><input type="text" data-path="britech" value="${credentials?.paths?.britech || ''}" />
                <label>MAPS</label><input type="text" data-path="maps" value="${credentials?.paths?.maps || ''}" />
                <label>FIDC</label><input type="text" data-path="fidc" value="${credentials?.paths?.fidc || ''}" />
                <label>QORE PDF</label><input type="text" data-path="qore_pdf" value="${credentials?.paths?.qore_pdf || ''}" />
                <label>QORE Excel</label><input type="text" data-path="qore_excel" value="${credentials?.paths?.qore_excel || ''}" />
                <label>TRUSTEE</label><input type="text" data-path="trustee" value="${credentials?.paths?.trustee || ''}" />
                <label>Selenium Temp</label><input type="text" data-path="selenium_temp" value="${credentials?.paths?.selenium_temp || ''}" />
              </div>
            </div>
          </div>
          <div class="cred-panel" id="panel-json">
            <textarea id="credentials-json" style="width: 100%; height: 400px; font-family: monospace; font-size: 11px; background: #0f0f23; color: #fff; border: 1px solid #333; border-radius: 8px; padding: 12px;">${JSON.stringify(credentials, null, 2)}</textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancelar</button>
          <button class="btn btn-primary" onclick="saveCredentialsFromModal()">💾 Salvar</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  } catch (error) {
    showToast('Erro ao carregar credenciais', 'error');
  }
};

(window as any).switchCredTab = (btn: HTMLElement, panelId: string) => {
  document.querySelectorAll('.cred-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.cred-panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('panel-' + panelId)?.classList.add('active');
};

(window as any).toggleFundosList = (sistema: string) => {
  const checkbox = document.getElementById(`${sistema}-usar-todos`) as HTMLInputElement;
  const list = document.getElementById(`${sistema}-fundos-list`);
  if (checkbox && list) {
    if (checkbox.checked) {
      list.classList.add('disabled');
    } else {
      list.classList.remove('disabled');
    }
  }
};

(window as any).saveCredentialsFromModal = async () => {
  // Check which panel is active
  const jsonPanel = document.getElementById('panel-json');
  const textarea = document.getElementById('credentials-json') as HTMLTextAreaElement;

  let credentials: any;

  if (jsonPanel?.classList.contains('active')) {
    // Save from JSON
    try {
      credentials = JSON.parse(textarea.value);
    } catch {
      showToast('JSON inválido', 'error');
      return;
    }
  } else {
    // Build from form fields
    credentials = JSON.parse(textarea.value); // Start with original

    // Update systems
    document.querySelectorAll('[data-system]').forEach((input: any) => {
      const system = input.dataset.system;
      const field = input.dataset.field;

      if (system.includes('amplis reag')) {
        if (!credentials.amplis) credentials.amplis = {};
        if (!credentials.amplis.reag) credentials.amplis.reag = {};
        credentials.amplis.reag[field] = input.value;
      } else if (system.includes('amplis master')) {
        if (!credentials.amplis) credentials.amplis = {};
        if (!credentials.amplis.master) credentials.amplis.master = {};
        credentials.amplis.master[field] = input.value;
      } else {
        const sysName = system.split(' ')[0];
        if (!credentials[sysName]) credentials[sysName] = {};
        credentials[sysName][field] = input.value;
      }
    });

    // Update paths
    document.querySelectorAll('[data-path]').forEach((input: any) => {
      if (!credentials.paths) credentials.paths = {};
      credentials.paths[input.dataset.path] = input.value;
    });

    // Update fund selections
    ['fidc', 'maps', 'qore'].forEach(sistema => {
      const usarTodosCheckbox = document.getElementById(`${sistema}-usar-todos`) as HTMLInputElement;
      if (usarTodosCheckbox) {
        credentials[sistema].usar_todos = usarTodosCheckbox.checked;

        // Get selected funds
        const selectedFundos: string[] = [];
        document.querySelectorAll(`[data-fundos="${sistema}"]:checked`).forEach((input: any) => {
          selectedFundos.push(input.value);
        });
        credentials[sistema].fundos_selecionados = selectedFundos;
      }
    });
  }

  try {
    const result = await api.saveCredentials(credentials);
    if (result.success) {
      showToast('Credenciais salvas!', 'success');
      document.querySelector('.modal')?.remove();
    } else {
      showToast('Erro: ' + result.error, 'error');
    }
  } catch {
    showToast('Erro ao salvar', 'error');
  }
};

function updateSistemaStatus(sistemaId: string, status: StatusUpdate): void {
  if (!config?.sistemas[sistemaId]) return;
  config.sistemas[sistemaId].status = status.status;
  config.sistemas[sistemaId].progresso = status.progresso;
  config.sistemas[sistemaId].mensagem = status.mensagem;

  const card = document.getElementById(`card-${sistemaId}`);
  if (card) {
    card.className = `system-card ${status.status === 'RUNNING' ? 'running' : (config.sistemas[sistemaId].ativo ? 'active' : 'inactive')}`;
    const progressBar = card.querySelector('.system-progress-bar') as HTMLElement;
    if (progressBar) {
      progressBar.style.width = `${status.progresso}%`;
    }
    const statusEl = card.querySelector('.system-status');
    if (statusEl) {
      statusEl.textContent = status.mensagem;
    }
  }
}

function showToast(message: string, type: 'success' | 'error' = 'success'): void {
  const toast = document.getElementById('toast');
  const icon = document.getElementById('toast-icon');
  const msg = document.getElementById('toast-message');

  if (toast && icon && msg) {
    toast.className = 'toast ' + type;
    icon.textContent = type === 'success' ? '✅' : '❌';
    msg.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  }
}

function setupEventListeners(): void {
  // Add any additional event listeners here
}

// Start the application
init();
