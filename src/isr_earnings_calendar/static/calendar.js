(function () {
  "use strict";

  const KNOWN_TYPES = new Set(["פרסום דוחות", "שיחת ועידה", "הנפקה"]);

  document.addEventListener("DOMContentLoaded", function () {
    const calendarEl = document.getElementById("calendar");
    const modal = document.getElementById("event-modal");
    const searchInput = document.getElementById("company-search");
    const typeCheckboxes = document.querySelectorAll(
      ".filter-item input[type='checkbox'][data-filter-type]",
    );

    const calendar = new FullCalendar.Calendar(calendarEl, {
      locale: "he",
      direction: "rtl",
      initialView: "dayGridMonth",
      firstDay: 0,
      headerToolbar: {
        start: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
        center: "title",
        end: "today prev,next",
      },
      buttonText: {
        today: "היום",
        month: "חודש",
        week: "שבוע",
        day: "יום",
        list: "רשימה",
      },
      height: "auto",
      nowIndicator: true,
      eventDisplay: "block",
      events: "/api/events",
      eventClick: function (info) {
        info.jsEvent.preventDefault();
        openEventModal(info.event);
      },
    });

    calendar.render();

    typeCheckboxes.forEach((cb) =>
      cb.addEventListener("change", applyFilters),
    );
    searchInput.addEventListener("input", applyFilters);

    function applyFilters() {
      const allowedTypes = new Set();
      let allowOther = false;
      typeCheckboxes.forEach((cb) => {
        if (!cb.checked) return;
        const v = cb.dataset.filterType;
        if (v === "__other__") allowOther = true;
        else allowedTypes.add(v);
      });
      const query = searchInput.value.trim().toLowerCase();

      calendar.getEvents().forEach((ev) => {
        const t = ev.extendedProps.event_type || "";
        const company = (ev.extendedProps.company_name || "").toLowerCase();
        const typeMatches = KNOWN_TYPES.has(t)
          ? allowedTypes.has(t)
          : allowOther;
        const queryMatches = !query || company.includes(query);
        ev.setProp("display", typeMatches && queryMatches ? "auto" : "none");
      });
    }

    function openEventModal(event) {
      const props = event.extendedProps || {};
      document.getElementById("modal-title").textContent = event.title;
      document.getElementById("modal-company").textContent =
        props.company_name || "—";
      document.getElementById("modal-type").textContent =
        props.event_type || "—";
      document.getElementById("modal-when").textContent = formatRange(
        event.start,
        event.end,
        event.allDay,
      );

      const descSection = document.getElementById("modal-description-section");
      const descEl = document.getElementById("modal-description");
      if (props.description) {
        descEl.textContent = props.description;
        descSection.hidden = false;
      } else {
        descEl.textContent = "";
        descSection.hidden = true;
      }

      const links = document.getElementById("modal-links");
      links.innerHTML = "";
      if (props.report_url) {
        links.appendChild(makeLink(props.report_url, "קישור לדיווח במאיה"));
      }
      if (props.source_url) {
        links.appendChild(makeLink(props.source_url, "מקור"));
      }

      if (typeof modal.showModal === "function") modal.showModal();
      else modal.setAttribute("open", "open");
    }

    function makeLink(href, text) {
      const a = document.createElement("a");
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = text;
      return a;
    }

    function formatRange(start, end, allDay) {
      if (!start) return "—";
      const dateOpts = { year: "numeric", month: "long", day: "numeric" };
      const timeOpts = { hour: "2-digit", minute: "2-digit" };
      const startDate = start.toLocaleDateString("he-IL", dateOpts);
      if (allDay) return startDate;
      const startTime = start.toLocaleTimeString("he-IL", timeOpts);
      if (!end) return `${startDate} ${startTime}`;
      const sameDay = end.toDateString() === start.toDateString();
      const endTime = end.toLocaleTimeString("he-IL", timeOpts);
      if (sameDay) return `${startDate} ${startTime}–${endTime}`;
      const endDate = end.toLocaleDateString("he-IL", dateOpts);
      return `${startDate} ${startTime} – ${endDate} ${endTime}`;
    }

    modal.addEventListener("click", function (e) {
      if (e.target.matches("[data-close-modal]") || e.target === modal) {
        modal.close();
      }
    });

    const copyBtn = document.getElementById("copy-ics");
    copyBtn.addEventListener("click", async function () {
      try {
        await navigator.clipboard.writeText(window.CALENDAR_CONFIG.ics_url);
        const original = copyBtn.textContent;
        copyBtn.textContent = "✓ הועתק";
        setTimeout(() => (copyBtn.textContent = original), 1500);
      } catch (e) {
        window.prompt("העתיקו את הקישור:", window.CALENDAR_CONFIG.ics_url);
      }
    });
  });
})();
