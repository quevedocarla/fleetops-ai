const API_CHAT = "/agent/chat";


const STATUS_LABELS = {
    "BLOCKED": "BLOQUEADA",
    "OK": "OK",
    "WAITING": "AGUARDANDO",
    "REVIEW": "EM REVISAO",
    "PENDING": "PENDENTE",
    "COMPLETED": "CONCLUIDA",
    "PROCESSED": "PROCESSADA",
    "ERROR": "ERRO",
    "ACTIVE": "ATIVO",
    "INACTIVE": "INATIVO",
    "INSTALLATION": "INSTALACAO",
    "MAINTENANCE": "MANUTENCAO",
    "CANCELLATION": "CANCELAMENTO"
};


function translateStatus(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }

    return (
        STATUS_LABELS[value]
        || value
    );
}


function translateProblem(problem) {

    if (!problem) {
        return problem;
    }

    let text = problem;

    text = text.replace(
        /Contract is inactive/gi,
        "Contrato inativo"
    );

    text = text.replace(
        /Contrato (\d+) esta inativo\./gi,
        "Contrato $1 está inativo."
    );

    text = text.replace(
        /Fila de processamento esta com erro:/gi,
        "Fila de processamento está com erro:"
    );

    return text;
}


function translateKnowledgeText(text) {

    if (!text) {
        return "";
    }

    let result = text;

    const replacements = [
        [/\bINACTIVE\b/gi, "inativo"],
        [/\bACTIVE\b/gi, "ativo"],
        [/\bBLOCKED\b/gi, "bloqueada"],
        [/\bPENDING\b/gi, "pendente"],
        [/\bERROR\b/gi, "erro"],
        [/\bWAITING\b/gi, "aguardando"],
        [/\bPROCESSED\b/gi, "processada"],
        [/\bCOMPLETED\b/gi, "concluída"],
        [/\bINSTALLATION\b/gi, "instalação"],
        [/\bMAINTENANCE\b/gi, "manutenção"],
        [/\bCANCELLATION\b/gi, "cancelamento"],
        [/\bOrdem de Servico\b/gi, "Ordem de Serviço"],
        [/\bServico\b/gi, "Serviço"],
        [/\bultima\b/gi, "última"],
        [/\bate\b/gi, "até"],
        [/\bsituacao\b/gi, "situação"],
        [/\bcontratual\b/gi, "contratual"],
        [/\binstalacao\b/gi, "instalação"],
        [/\baplicaveis\b/gi, "aplicáveis"]
    ];

    replacements.forEach(
        ([pattern, value]) => {
            result = result.replace(
                pattern,
                value
            );
        }
    );

    return result;
}


function translateResponseMode(mode) {

    switch (mode) {

        case "DIRECT":
            return "Resposta direta";

        case "DEGRADED":
            return "Modo degradado";

        case "AI":
            return "Análise com IA";

        case "OUT_OF_SCOPE":
            return "Fora do escopo";

        default:
            return mode || "-";
    }
}


const chatMessages =
    document.getElementById(
        "chat-messages"
    );

const chatForm =
    document.getElementById(
        "chat-form"
    );

const messageInput =
    document.getElementById(
        "message-input"
    );

const sendButton =
    document.getElementById(
        "send-button"
    );

const newChatButton =
    document.getElementById(
        "new-chat-button"
    );

const threadIdElement =
    document.getElementById(
        "thread-id"
    );

const warningBox =
    document.getElementById(
        "warning-box"
    );

const warningContent =
    document.getElementById(
        "warning-content"
    );

const systemStatus =
    document.getElementById(
        "system-status"
    );


function generateThreadId() {

    if (
        window.crypto &&
        crypto.randomUUID
    ) {
        return crypto.randomUUID();
    }

    return (
        "thread-" +
        Date.now()
    );
}


function getThreadId() {

    let threadId =
        localStorage.getItem(
            "fleetops_thread_id"
        );

    if (!threadId) {

        threadId =
            generateThreadId();

        localStorage.setItem(
            "fleetops_thread_id",
            threadId
        );
    }

    return threadId;
}


function setThreadId(threadId) {

    localStorage.setItem(
        "fleetops_thread_id",
        threadId
    );

    threadIdElement.textContent =
        threadId;
}


function appendMessage(
    role,
    text,
    type = "",
    metadata = null
) {

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        `message ${role} ${type}`;

    const roleElement =
        document.createElement(
            "div"
        );

    roleElement.className =
        "message-role";

    roleElement.textContent =
        role === "user"
            ? "Você"
            : "FleetOps AI";

    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        "message-bubble";

    bubble.textContent =
        text;

    wrapper.appendChild(
        roleElement
    );

    wrapper.appendChild(
        bubble
    );


    if (
        role === "assistant" &&
        metadata
    ) {

        const meta =
            document.createElement(
                "div"
            );

        meta.className =
            "message-meta";


        let modeText =
            "✨ Análise com IA";


        if (
            metadata.responseMode
            === "DIRECT"
        ) {
            modeText =
                "⚡ Resposta direta";
        }


        if (
            metadata.responseMode
            === "DEGRADED"
        ) {
            modeText =
                "⚠ Resposta em modo degradado";
        }


        if (
            metadata.responseMode
            === "OUT_OF_SCOPE"
        ) {
            modeText =
                "↩ Fora do escopo";
        }


        const timeText =
            metadata.durationMs >= 1000
                ? (
                    metadata.durationMs
                    / 1000
                ).toFixed(2) + " s"
                : Math.round(
                    metadata.durationMs
                ) + " ms";


        const summary =
            document.createElement(
                "span"
            );

        summary.textContent =
            `${modeText} • ${timeText}`;

        meta.appendChild(
            summary
        );


        const details =
            document.createElement(
                "details"
            );

        details.className =
            "technical-details";


        const detailsSummary =
            document.createElement(
                "summary"
            );

        detailsSummary.textContent =
            "Ver detalhes técnicos";

        details.appendChild(
            detailsSummary
        );


        const technicalContent =
            document.createElement(
                "div"
            );

        technicalContent.className =
            "technical-details-content";


        const traceRow =
            document.createElement(
                "div"
            );

        traceRow.innerHTML =
            "<strong>Trace ID</strong>";

        const traceCode =
            document.createElement(
                "code"
            );

        traceCode.textContent =
            metadata.traceId || "-";

        traceRow.appendChild(
            traceCode
        );


        const processRow =
            document.createElement(
                "div"
            );

        processRow.innerHTML =
            "<strong>Processamento</strong>";

        const processSpan =
            document.createElement(
                "span"
            );

        processSpan.textContent =
            translateResponseMode(
                metadata.responseMode
            );

        processRow.appendChild(
            processSpan
        );


        const modeRow =
            document.createElement(
                "div"
            );

        modeRow.innerHTML =
            "<strong>Modo</strong>";

        const modeSpan =
            document.createElement(
                "span"
            );

        modeSpan.textContent =
            metadata.degraded
                ? "Degradado"
                : "Normal";

        modeRow.appendChild(
            modeSpan
        );


        const timeRow =
            document.createElement(
                "div"
            );

        timeRow.innerHTML =
            "<strong>Tempo</strong>";

        const timeSpan =
            document.createElement(
                "span"
            );

        timeSpan.textContent =
            timeText;

        timeRow.appendChild(
            timeSpan
        );


        technicalContent.appendChild(
            traceRow
        );

        technicalContent.appendChild(
            processRow
        );

        technicalContent.appendChild(
            modeRow
        );

        technicalContent.appendChild(
            timeRow
        );


        if (
            metadata.sources &&
            metadata.sources.length > 0
        ) {

            const sourcesTitle =
                document.createElement(
                    "div"
                );


            sourcesTitle.className =
                "sources-title";


            sourcesTitle.textContent =
                "Conhecimento consultado";


            technicalContent.appendChild(
                sourcesTitle
            );


            metadata.sources.forEach(
                source => {

                    const sourceCard =
                        document.createElement(
                            "div"
                        );


                    sourceCard.className =
                        "source-card";


                    const sourceName =
                        document.createElement(
                            "strong"
                        );


                    sourceName.textContent =
                        source.source
                        || "Fonte";


                    const similarity =
                        document.createElement(
                            "span"
                        );


                    if (
                        source.similarity !== null &&
                        source.similarity !== undefined
                    ) {

                        similarity.textContent =
                            `Similaridade: ${(
                                source.similarity
                                * 100
                            ).toFixed(1)}%`;

                    }


                    const sourceContent =
                        document.createElement(
                            "p"
                        );


                    sourceContent.textContent =
                        translateKnowledgeText(
                            source.content
                            || ""
                        );


                    sourceCard.appendChild(
                        sourceName
                    );


                    sourceCard.appendChild(
                        similarity
                    );


                    sourceCard.appendChild(
                        sourceContent
                    );


                    technicalContent.appendChild(
                        sourceCard
                    );

                }
            );

        }


        details.appendChild(
            technicalContent
        );

        meta.appendChild(
            details
        );

        wrapper.appendChild(
            meta
        );
    }


    chatMessages.appendChild(
        wrapper
    );

    chatMessages.scrollTop =
        chatMessages.scrollHeight;

    return wrapper;
}


function showWelcomeMessage() {

    appendMessage(
        "assistant",
        (
            "Olá! Eu sou o FleetOps AI. " +
            "Você pode perguntar, por exemplo:\n\n" +
            "• Por que a OS 10235 está bloqueada?\n" +
            "• Qual é o contrato dela?\n" +
            "• Qual é a placa?\n" +
            "• Qual o status da fila?"
        )
    );
}


function setLoading(loading) {

    sendButton.disabled =
        loading;

    messageInput.disabled =
        loading;

    sendButton.textContent =
        loading
            ? "Analisando..."
            : "Enviar";
}


function updateWarnings(
    degraded,
    warnings
) {

    warningContent.textContent =
        "";

    if (
        !degraded ||
        !warnings ||
        warnings.length === 0
    ) {

        warningBox.classList.add(
            "hidden"
        );

        document.getElementById(
            "execution-mode"
        ).textContent =
            "Normal";

        return;
    }


    warningBox.classList.remove(
        "hidden"
    );


    warnings.forEach(
        warning => {

            const line =
                document.createElement(
                    "div"
                );

            line.textContent =
                warning;

            warningContent.appendChild(
                line
            );
        }
    );


    document.getElementById(
        "execution-mode"
    ).textContent =
        "Degradado";
}


function setSystemOnline(online) {

    if (online) {

        systemStatus.classList.remove(
            "offline"
        );

        systemStatus.classList.add(
            "online"
        );

        systemStatus.lastChild.textContent =
            " Online";
    }

    else {

        systemStatus.classList.remove(
            "online"
        );

        systemStatus.classList.add(
            "offline"
        );

        systemStatus.lastChild.textContent =
            " Indisponível";
    }
}


function setDiagnosticBadge(status) {

    const badge =
        document.getElementById(
            "diagnostic-badge"
        );

    badge.textContent =
        status
            ? translateStatus(status)
            : "SEM CONTEXTO";

    badge.className =
        "diagnostic-badge";


    switch (status) {

        case "BLOCKED":

            badge.classList.add(
                "blocked"
            );

            break;


        case "OK":

            badge.classList.add(
                "ok"
            );

            break;


        case "WAITING":

            badge.classList.add(
                "waiting"
            );

            break;


        default:

            badge.classList.add(
                "neutral"
            );
    }
}


function resetContext() {

    const ids = [
        "context-os",
        "context-status",
        "context-type",
        "context-plate",
        "context-contract",
        "context-contract-status",
        "context-queue",
        "trace-id"
    ];


    ids.forEach(
        id => {

            document.getElementById(
                id
            ).textContent =
                "-";
        }
    );


    document.getElementById(
        "execution-mode"
    ).textContent =
        "Normal";


    setDiagnosticBadge(
        null
    );


    const problems =
        document.getElementById(
            "problems-list"
        );


    problems.textContent =
        "";


    const empty =
        document.createElement(
            "div"
        );

    empty.className =
        "empty-state";

    empty.textContent =
        "Nenhum diagnóstico carregado.";

    problems.appendChild(
        empty
    );


    updateWarnings(
        false,
        []
    );
}


async function loadDiagnostic(
    serviceOrderId
) {

    try {

        const response =
            await fetch(
                `/service-orders/${serviceOrderId}/diagnostic`
            );


        if (!response.ok) {

            throw new Error(
                "Não foi possível carregar o diagnóstico."
            );
        }


        const data =
            await response.json();


        const serviceOrder =
            data.service_order || {};

        const contract =
            data.contract || {};

        const queue =
            data.queue || {};


        document.getElementById(
            "context-os"
        ).textContent =
            serviceOrder.id
            ?? serviceOrderId;


        document.getElementById(
            "context-status"
        ).textContent =
            translateStatus(
                serviceOrder.status
            );


        document.getElementById(
            "context-type"
        ).textContent =
            translateStatus(
                serviceOrder.type
            );


        document.getElementById(
            "context-plate"
        ).textContent =
            serviceOrder.vehicle_plate
            ?? "-";


        document.getElementById(
            "context-contract"
        ).textContent =
            contract.id
            ?? "-";


        document.getElementById(
            "context-contract-status"
        ).textContent =
            translateStatus(
                contract.status
            );


        document.getElementById(
            "context-queue"
        ).textContent =
            queue.status
                ? translateStatus(
                    queue.status
                )
                : "SEM FILA";


        setDiagnosticBadge(
            data.diagnostic_status
        );


        renderProblems(
            data.problems || []
        );
    }

    catch (error) {

        console.error(
            error
        );
    }
}


function renderProblems(problems) {

    const container =
        document.getElementById(
            "problems-list"
        );


    container.textContent =
        "";


    if (
        !problems ||
        problems.length === 0
    ) {

        const empty =
            document.createElement(
                "div"
            );

        empty.className =
            "empty-state";

        empty.textContent =
            "Nenhum problema encontrado.";

        container.appendChild(
            empty
        );

        return;
    }


    problems.forEach(
        problem => {

            const element =
                document.createElement(
                    "div"
                );

            element.className =
                "problem";

            element.textContent =
                translateProblem(
                    problem
                );

            container.appendChild(
                element
            );
        }
    );
}


async function sendMessage(message) {

    const threadId =
        getThreadId();


    appendMessage(
        "user",
        message
    );


    const typing =
        appendMessage(
            "assistant",
            "Analisando...",
            "typing"
        );


    setLoading(
        true
    );


    const requestStart =
        performance.now();


    try {

        const response =
            await fetch(
                API_CHAT,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                thread_id:
                                    threadId,

                                message:
                                    message
                            }
                        )
                }
            );


        const data =
            await response.json();


        const requestDuration =
            performance.now()
            -
            requestStart;


        typing.remove();


        if (
            !response.ok
        ) {

            const detail =
                data.detail || {};


            const errorMessage =
                detail.message
                ||
                "Não foi possível processar a solicitação.";


            appendMessage(
                "assistant",
                errorMessage,
                "error"
            );


            if (
                detail.trace_id
            ) {

                document.getElementById(
                    "trace-id"
                ).textContent =
                    detail.trace_id;
            }


            setSystemOnline(
                response.status !== 503
            );


            return;
        }


        setSystemOnline(
            true
        );


        appendMessage(
            "assistant",
            data.answer,
            "",
            {
                responseMode:
                    data.response_mode,

                durationMs:
                    requestDuration,

                traceId:
                    data.trace_id,

                degraded:
                    data.degraded,

                sources:
                    data.sources
                    || []
            }
        );


        document.getElementById(
            "trace-id"
        ).textContent =
            data.trace_id
            || "-";


        updateWarnings(
            data.degraded,
            data.warnings
        );


        if (
            data.service_order_id
        ) {

            await loadDiagnostic(
                data.service_order_id
            );
        }
    }

    catch (error) {

        typing.remove();


        appendMessage(
            "assistant",
            (
                "Não foi possível conectar ao FleetOps AI. " +
                "Verifique se a API está disponível."
            ),
            "error"
        );


        setSystemOnline(
            false
        );


        console.error(
            error
        );
    }

    finally {

        setLoading(
            false
        );


        messageInput.focus();
    }
}


chatForm.addEventListener(
    "submit",

    async event => {

        event.preventDefault();


        const message =
            messageInput.value.trim();


        if (!message) {
            return;
        }


        messageInput.value =
            "";


        await sendMessage(
            message
        );
    }
);


messageInput.addEventListener(
    "keydown",

    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            chatForm.requestSubmit();
        }
    }
);


newChatButton.addEventListener(
    "click",

    () => {

        const newThreadId =
            generateThreadId();


        setThreadId(
            newThreadId
        );


        chatMessages.textContent =
            "";


        resetContext();


        showWelcomeMessage();


        messageInput.focus();
    }
);


function initialize() {

    const threadId =
        getThreadId();


    setThreadId(
        threadId
    );


    resetContext();


    showWelcomeMessage();


    messageInput.focus();
}


initialize();
