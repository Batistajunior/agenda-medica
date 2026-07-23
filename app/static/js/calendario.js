document.addEventListener("DOMContentLoaded", () => {
    const calendarioEl = document.getElementById("calendario");

    const calendario = new FullCalendar.Calendar(calendarioEl, {
        initialView: "dayGridMonth",
        locale: "pt-br",
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
        },
        buttonText: {
            today: "Hoje",
            month: "Mês",
            week: "Semana",
            day: "Dia",
            list: "Lista",
        },
        height: "auto",
        navLinks: true,
        editable: false,
        dayMaxEvents: true,
        events: "/api/agenda/calendario",
        eventClick(info) {
            info.jsEvent.preventDefault();

            if (info.event.url) {
                window.location.href = info.event.url;
            }
        },
        eventDidMount(info) {
            const status = info.event.extendedProps.status;

            if (status) {
                info.el.setAttribute("title", `${info.event.title} (${status})`);
            }
        },
    });

    calendario.render();
});
