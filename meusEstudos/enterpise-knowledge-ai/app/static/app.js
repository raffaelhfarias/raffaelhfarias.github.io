"use strict";

const fileInput = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const fileError = document.querySelector("#file-error");
const question = document.querySelector("#question");
const send = document.querySelector("#send-question");
const announcement = document.querySelector("#announcement");
const history = document.querySelector("#history");
let session = null;
let busy = false;
const messages = {
  demo_disabled: "A demo está desativada no servidor. A interface está disponível para visualização.",
  demo_hourly_limit: "A cota compartilhada desta hora foi atingida. Tente novamente mais tarde.",
  demo_provider_unavailable: "A IA não respondeu. Tente mais tarde. Uma pergunta enviada conta como tentativa, mesmo se falhar.",
  demo_database_unavailable: "O banco da demo está indisponível. Tente novamente mais tarde.",
  same_origin_required: "Abra a demo pelo endereço original e tente novamente.",
  demo_session_expired: "A sessão expirou. Envie novamente um documento para começar.",
  demo_session_required: "Selecione um documento para começar.",
  session_busy_or_question_limit: "Há uma pergunta em andamento ou as cinco tentativas já foram usadas.",
  remove_current_document_first: "Remova o documento atual antes de enviar outro.",
  document_not_readable_or_too_long: "Não foi possível extrair o texto. Use PDF textual ou DOCX curto (até 80 trechos); imagens e PDFs escaneados não são suportados.",
  request_too_large: "O arquivo ultrapassa o limite do servidor. Escolha um documento menor.",
  pdf_page_limit_exceeded: "O PDF ultrapassa o limite de páginas. Escolha um documento menor.",
  invalid_question: "Escreva uma pergunta com até 1000 caracteres.",
  empty_file: "O arquivo está vazio. Selecione outro documento.",
  unsupported_file_type: "Formato não suportado. Escolha um PDF textual ou DOCX válido.",
  invalid_pdf: "O PDF está inválido ou não pode ser aberto. Selecione outro documento.",
  invalid_docx: "O DOCX está inválido ou não pode ser aberto. Selecione outro documento.",
  docx_expanded_size_exceeded: "O conteúdo descompactado do DOCX é grande demais. Use um documento menor.",
};

async function api(path, options = {}) {
  const response = await fetch(`/v1/demo/${path}`, {
    ...options, credentials: "same-origin", cache: "no-store",
    headers: { "X-Demo-Request": "1", ...options.headers },
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(messages[data?.detail] || "Não foi possível concluir. Confira a conexão e tente novamente.");
    error.status = response.status;
    throw error;
  }
  return data;
}

function showError(error) {
  fileError.textContent = error.message;
  fileError.hidden = false;
}

function render() {
  document.querySelector("#selected-file").hidden = !session;
  document.querySelector("#empty-state").hidden = Boolean(session);
  document.querySelector("#example-state").hidden = !session;
  document.querySelector("#choose-file").disabled = busy || Boolean(session);
  document.querySelector("#use-example").disabled = busy || Boolean(session);
  document.querySelector("#remove-file").disabled = busy;
  question.disabled = busy || !session || session.busy || session.questions_remaining <= 0;
  send.disabled = question.disabled || !question.value.trim();
  document.querySelector("#quota-text").textContent = session
    ? `${session.questions_remaining} de 5 perguntas restantes` : "Até 5 perguntas por sessão";
  document.querySelectorAll(".quota-dots i").forEach((dot, index) => {
    dot.classList.toggle("used", Boolean(session) && index >= session.questions_remaining);
  });
  document.querySelector("#workspace-label").textContent = busy ? "Processando…" : "Área de perguntas";
  document.querySelector("#workspace").setAttribute("aria-busy", String(busy));
  if (session) {
    document.querySelector("#file-name").textContent = session.filename;
    document.querySelector("#file-meta").textContent = "Documento da sessão · temporário";
    document.querySelector("#file-status").textContent = "Texto processado. Sessão válida por 30 minutos a partir do envio.";
  }
  document.querySelector("#connection-note").textContent = busy || session?.busy
    ? "Aguarde. O processamento pode levar alguns minutos; não reenvie a solicitação."
    : session?.questions_remaining === 0
      ? "Você usou as cinco tentativas desta sessão. Confira as respostas e suas fontes."
      : "Cada envio conta como tentativa, mesmo se a IA falhar. A demo tem uma cota compartilhada por hora.";
}

async function startDocument(file) {
  if (busy || session) return;
  if (file) {
    if (!/\.(pdf|docx)$/i.test(file.name)) return showError(new Error("Escolha um PDF ou DOCX."));
    if (!file.size) return showError(new Error("O arquivo está vazio."));
    if (file.size > 20 * 1024 * 1024) return showError(new Error("O arquivo ultrapassa 20 MB."));
  }
  busy = true;
  fileError.hidden = true;
  announcement.textContent = "Extraindo o texto e preparando a busca semântica. Aguarde.";
  render();
  try {
    session = file
      ? await api(`document?filename=${encodeURIComponent(file.name)}`, {
        method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: file,
      })
      : await api("example", { method: "POST" });
    history.replaceChildren();
    announcement.textContent = "Documento pronto. Você pode fazer cinco perguntas.";
  } catch (error) {
    showError(error);
  } finally {
    busy = false;
    fileInput.value = "";
    render();
    if (session) question.focus();
  }
}

function appendAnswer(text, result) {
  const article = document.createElement("article");
  article.className = "answer";
  const heading = document.createElement("h2");
  heading.textContent = text;
  const answer = document.createElement("p");
  answer.textContent = result.answer;
  article.append(heading, answer);
  result.sources.forEach((source) => {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `${session.filename} · ${source.page ? `página ${source.page}` : source.id}`;
    const quote = document.createElement("blockquote");
    quote.textContent = source.text;
    details.append(summary, quote);
    article.append(details);
  });
  if (!result.sources.length) {
    const note = document.createElement("p");
    note.className = "muted";
    note.textContent = "Sem evidência suficiente no documento.";
    article.append(note);
  }
  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "text-button";
  copy.textContent = "Copiar resposta";
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(result.answer);
      copy.textContent = "Resposta copiada";
    } catch {
      announcement.textContent = "Não foi possível copiar. Selecione o texto da resposta.";
    }
  });
  article.append(copy);
  history.append(article);
}

async function refreshSession() {
  try {
    session = await api("session");
  } catch (error) {
    if ([401, 410].includes(error.status)) session = null;
    else throw error;
  }
}

send.addEventListener("click", async () => {
  if (send.disabled) return;
  const text = question.value.trim();
  busy = true;
  fileError.hidden = true;
  render();
  announcement.textContent = "Buscando evidências e elaborando a resposta.";
  try {
    const result = await api("questions", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text }),
    });
    appendAnswer(text, result);
    session.questions_remaining = result.questions_remaining;
    question.value = "";
    announcement.textContent = `Resposta recebida. ${result.questions_remaining} perguntas restantes.`;
  } catch (error) {
    showError(error);
    try { await refreshSession(); } catch { session = null; }
  } finally {
    busy = false;
    render();
    if (!question.disabled) question.focus();
  }
});

question.addEventListener("input", render);
question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send.click(); }
});
document.querySelector("#choose-file").addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => startDocument(fileInput.files[0]));
document.querySelector("#use-example").addEventListener("click", () => startDocument(null));
document.querySelector("#remove-file").addEventListener("click", async () => {
  busy = true;
  render();
  try {
    await api("session", { method: "DELETE" });
    session = null;
    history.replaceChildren();
    question.value = "";
    fileError.hidden = true;
    announcement.textContent = "Documento e trechos removidos do servidor.";
  } catch (error) { showError(error); }
  finally { busy = false; render(); }
});
["dragenter", "dragover", "dragleave", "drop"].forEach((name) => {
  dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    dropzone.classList.toggle("drag-over", ["dragenter", "dragover"].includes(name));
    if (name === "drop" && !busy && !session) {
      if (event.dataTransfer.files.length === 1) startDocument(event.dataTransfer.files[0]);
      else showError(new Error("Selecione apenas um documento por vez."));
    }
  });
});
busy = true;
render();
refreshSession().catch(showError).finally(() => {
  busy = false;
  render();
});
