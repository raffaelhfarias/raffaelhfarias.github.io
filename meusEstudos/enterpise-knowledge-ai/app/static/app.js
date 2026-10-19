"use strict";

const fileInput = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const selectedFile = document.querySelector("#selected-file");
const fileError = document.querySelector("#file-error");
const emptyState = document.querySelector("#empty-state");
const exampleState = document.querySelector("#example-state");
const announcement = document.querySelector("#announcement");
const copyButton = document.querySelector("#copy-answer");
const examples = {
  deadline: {
    answer: "O reembolso deve ser solicitado em até 15 dias corridos após a despesa. O pedido precisa incluir a nota fiscal e ser enviado ao financeiro.",
    quote: "O prazo para solicitar reembolso é de 15 dias corridos após a despesa. O pedido deve conter nota fiscal e ser enviado ao financeiro.",
  },
  approver: {
    answer: "A aprovação da solicitação de reembolso cabe à gestora Marina.",
    quote: "A aprovação cabe à gestora Marina.",
  },
  unknown: {
    answer: "Não encontrei informações suficientes no documento para responder sobre o salário da gestora.",
    quote: null,
  },
};

function showExampleAnswer(identifier) {
  const example = examples[identifier];
  document.querySelector("#sample-answer").textContent = example.answer;
  document.querySelector("#source-quote").textContent = example.quote || "";
  document.querySelector("#source-detail").hidden = !example.quote;
  document.querySelector("#no-source").hidden = Boolean(example.quote);
  document.querySelector("#source-count").textContent = example.quote ? "1 trecho de exemplo" : "Sem evidência no exemplo";
  document.querySelectorAll("[data-example]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.example === identifier));
  });
  copyButton.textContent = "Copiar resposta";
}

function showFile(name, metadata, status) {
  document.querySelector("#file-name").textContent = name;
  document.querySelector("#file-meta").textContent = metadata;
  document.querySelector("#file-status").textContent = status;
  selectedFile.hidden = false;
  fileError.hidden = true;
}

function selectFile(file) {
  if (!file) return;
  const extension = file.name.split(".").pop().toLowerCase();
  let error = "";
  if (!["pdf", "docx"].includes(extension)) error = "Escolha um arquivo PDF ou DOCX.";
  else if (file.size === 0) error = "O arquivo está vazio. Selecione outro documento.";
  else if (file.size > 20 * 1024 * 1024) error = "O arquivo ultrapassa 20 MB. Escolha um documento menor.";
  if (error) {
    fileInput.value = "";
    fileError.textContent = error;
    fileError.hidden = false;
    return;
  }
  showFile(file.name, `${extension.toUpperCase()} · ${(file.size / 1024 / 1024).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} MB`, "Selecionado apenas no navegador. O processamento será habilitado após integrar a API.");
  emptyState.hidden = false;
  exampleState.hidden = true;
  document.querySelector("#workspace-label").textContent = "Documento selecionado · conexão pendente";
  announcement.textContent = `${file.name} selecionado. Nenhum arquivo foi enviado.`;
}

document.querySelector("#choose-file").addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));
document.querySelector("#remove-file").addEventListener("click", () => {
  fileInput.value = "";
  selectedFile.hidden = true;
  fileError.hidden = true;
  exampleState.hidden = true;
  emptyState.hidden = false;
  document.querySelector("#workspace-label").textContent = "Área de perguntas";
  announcement.textContent = "Documento removido da prévia.";
  document.querySelector("#choose-file").focus();
});

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("drag-over");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("drag-over");
  });
});
dropzone.addEventListener("drop", (event) => {
  fileInput.value = "";
  if (event.dataTransfer.files.length > 1) {
    fileError.textContent = "Selecione apenas um documento por vez.";
    fileError.hidden = false;
    return;
  }
  selectFile(event.dataTransfer.files[0]);
});

document.querySelector("#use-example").addEventListener("click", () => {
  fileInput.value = "";
  showFile("Manual da equipe Aurora", "Documento fictício", "Exemplo visual local. Nenhum processamento ou chamada à NVIDIA é realizado.");
  emptyState.hidden = true;
  exampleState.hidden = false;
  document.querySelector("#workspace-label").textContent = "Explorando um exemplo visual";
  showExampleAnswer("deadline");
  announcement.textContent = "Exemplo visual aberto. As respostas são pré-definidas, não geradas por IA.";
  document.querySelector("[data-example]").focus({ preventScroll: true });
  if (window.matchMedia("(max-width: 720px)").matches) exampleState.scrollIntoView({ block: "start" });
});
document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => showExampleAnswer(button.dataset.example));
});
copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(`Resposta ilustrativa, não gerada por IA:\n${document.querySelector("#sample-answer").textContent}`);
    copyButton.textContent = "Copiada";
    announcement.textContent = "Resposta ilustrativa copiada.";
  } catch {
    announcement.textContent = "Não foi possível copiar automaticamente. Selecione o texto da resposta para copiá-lo.";
    copyButton.textContent = "Selecione o texto para copiar";
  }
});
document.querySelector(".about-link").addEventListener("click", () => {
  document.querySelector("#how-it-works").open = true;
});
