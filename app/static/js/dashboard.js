const CORES_STATUS = {
    Agendado: "#ffc107",
    Confirmado: "#198754",
    "Concluído": "#0d6efd",
    Cancelado: "#dc3545",
    Faltou: "#6c757d",
};

let graficoStatus = null;
let graficoSemanal = null;

function statusCss(status) {
    return status
        .toLowerCase()
        .replace(/í/g, "i")
        .replace(/ú/g, "u")
        .replace(/ã/g, "a")
        .replace(/ç/g, "c")
        .replace(/ /g, "-");
}

function debounce(funcao, atraso) {
    let timer;

    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => funcao(...args), atraso);
    };
}

function obterFiltros() {
    return {
        search: document.getElementById("search").value.trim(),
        status: document.getElementById("status").value,
        data_inicio: document.getElementById("data_inicio").value,
        data_fim: document.getElementById("data_fim").value,
    };
}

function montarQueryString(filtros) {
    const params = new URLSearchParams();

    Object.entries(filtros).forEach(([chave, valor]) => {
        if (valor) {
            params.set(chave, valor);
        }
    });

    return params.toString();
}

function atualizarContador(total) {
    document.getElementById("total-registros").textContent =
        `${total} registro(s) encontrado(s)`;
}

function renderizarTabela(agendamentos) {
    const tbody = document.getElementById("agenda-tbody");
    const tabelaWrapper = document.getElementById("tabela-wrapper");
    const emptyState = document.getElementById("agenda-empty");
    const modalsContainer = document.getElementById("modals-container");

    tbody.innerHTML = "";
    modalsContainer.innerHTML = "";

    if (!agendamentos.length) {
        tabelaWrapper.classList.add("d-none");
        emptyState.classList.remove("d-none");
        return;
    }

    tabelaWrapper.classList.remove("d-none");
    emptyState.classList.add("d-none");

    agendamentos.forEach((item) => {
        const cssStatus = statusCss(item.status);

        tbody.insertAdjacentHTML(
            "beforeend",
            `
            <tr>
                <td>${item.data}</td>
                <td><strong>${item.horario}</strong></td>
                <td>
                    <div class="patient-name">${item.paciente}</div>
                    <div class="patient-document">CPF: ${item.cpf}</div>
                </td>
                <td>${item.medico}</td>
                <td>${item.especialidade}</td>
                <td>${item.convenio || "Particular"}</td>
                <td>
                    <span class="status-badge status-${cssStatus}">
                        ${item.status}
                    </span>
                </td>
                <td class="text-end">
                    <div class="action-buttons">
                        <a
                            href="/agenda/${item.id}"
                            class="btn btn-sm btn-outline-secondary"
                            title="Ver detalhes"
                            aria-label="Ver detalhes"
                        >
                            <i class="bi bi-eye"></i>
                        </a>
                        <a
                            href="/agenda/${item.id}/editar"
                            class="btn btn-sm btn-outline-primary"
                            title="Editar"
                            aria-label="Editar"
                        >
                            <i class="bi bi-pencil"></i>
                        </a>
                        <button
                            type="button"
                            class="btn btn-sm btn-outline-danger"
                            title="Excluir"
                            aria-label="Excluir"
                            data-bs-toggle="modal"
                            data-bs-target="#modalExcluir${item.id}"
                        >
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
            `
        );

        modalsContainer.insertAdjacentHTML(
            "beforeend",
            `
            <div
                class="modal fade"
                id="modalExcluir${item.id}"
                tabindex="-1"
                aria-labelledby="tituloModalExcluir${item.id}"
                aria-hidden="true"
            >
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2
                                class="modal-title fs-5"
                                id="tituloModalExcluir${item.id}"
                            >
                                Excluir agendamento
                            </h2>
                            <button
                                type="button"
                                class="btn-close"
                                data-bs-dismiss="modal"
                                aria-label="Fechar"
                            ></button>
                        </div>
                        <div class="modal-body">
                            Confirma a exclusão do agendamento de
                            <strong>${item.paciente}</strong>
                            em
                            <strong>${item.data} às ${item.horario}</strong>?
                        </div>
                        <div class="modal-footer">
                            <button
                                type="button"
                                class="btn btn-outline-secondary"
                                data-bs-dismiss="modal"
                            >
                                Cancelar
                            </button>
                            <form method="POST" action="/agenda/${item.id}/excluir">
                                <button type="submit" class="btn btn-danger">
                                    <i class="bi bi-trash me-1"></i>
                                    Excluir
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            `
        );
    });
}

async function carregarAgendamentos() {
    const filtros = obterFiltros();
    const query = montarQueryString(filtros);

    try {
        const response = await fetch(`/api/agenda?${query}`);
        const resultado = await response.json();

        if (!resultado.success) {
            throw new Error(resultado.message || "Erro ao carregar dados.");
        }

        renderizarTabela(resultado.data);
        atualizarContador(resultado.total);
    } catch (erro) {
        console.error(erro);
    }
}

function renderizarGraficos(dados) {
    const ctxStatus = document.getElementById("grafico-status");
    const ctxSemanal = document.getElementById("grafico-semanal");

    const labelsStatus = Object.keys(dados.status_hoje);
    const valoresStatus = Object.values(dados.status_hoje);
    const coresPizza = labelsStatus.map(
        (status) => dados.cores_status[status] || "#0d6efd"
    );

    if (graficoStatus) {
        graficoStatus.destroy();
    }

    if (graficoSemanal) {
        graficoSemanal.destroy();
    }

    graficoStatus = new Chart(ctxStatus, {
        type: "doughnut",
        data: {
            labels: labelsStatus.length ? labelsStatus : ["Sem consultas"],
            datasets: [
                {
                    data: valoresStatus.length ? valoresStatus : [1],
                    backgroundColor: labelsStatus.length
                        ? coresPizza
                        : ["#dee2e6"],
                    borderWidth: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                },
            },
        },
    });

    graficoSemanal = new Chart(ctxSemanal, {
        type: "bar",
        data: {
            labels: dados.consultas_por_dia.labels,
            datasets: [
                {
                    label: "Consultas",
                    data: dados.consultas_por_dia.valores,
                    backgroundColor: "rgba(13, 110, 253, 0.7)",
                    borderColor: "#0d6efd",
                    borderWidth: 1,
                    borderRadius: 8,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                    },
                },
            },
        },
    });
}

async function carregarEstatisticas() {
    try {
        const response = await fetch("/api/dashboard/stats");
        const dados = await response.json();

        if (!dados.success) {
            throw new Error(dados.message || "Erro ao carregar gráficos.");
        }

        renderizarGraficos(dados);
    } catch (erro) {
        console.error(erro);
    }
}

function limparFiltros() {
    document.getElementById("search").value = "";
    document.getElementById("status").value = "";
    document.getElementById("data_inicio").value = "";
    document.getElementById("data_fim").value = "";
    carregarAgendamentos();
}

function configurarExportacao() {
    document.getElementById("btn-export-excel").addEventListener("click", () => {
        const query = montarQueryString(obterFiltros());
        window.location.href = `/agenda/exportar/excel?${query}`;
    });

    document.getElementById("btn-export-pdf").addEventListener("click", () => {
        const query = montarQueryString(obterFiltros());
        window.location.href = `/agenda/exportar/pdf?${query}`;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("filtro-form");
    const campoBusca = document.getElementById("search");

    formulario.addEventListener("submit", (evento) => {
        evento.preventDefault();
        carregarAgendamentos();
    });

    campoBusca.addEventListener(
        "input",
        debounce(() => carregarAgendamentos(), 350)
    );

    document.getElementById("status").addEventListener("change", carregarAgendamentos);
    document.getElementById("data_inicio").addEventListener("change", carregarAgendamentos);
    document.getElementById("data_fim").addEventListener("change", carregarAgendamentos);
    document.getElementById("btn-limpar").addEventListener("click", (evento) => {
        evento.preventDefault();
        limparFiltros();
    });

    configurarExportacao();
    carregarEstatisticas();
    carregarAgendamentos();
});
