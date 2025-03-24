document.addEventListener('DOMContentLoaded', () => {
    const calendarEl = document.getElementById('calendar');
    const form = document.getElementById('postForm');
    const exportBtn = document.getElementById('exportBtn');
    const viewMonthBtn = document.getElementById('viewMonthBtn');
    const viewWeekBtn = document.getElementById('viewWeekBtn');
    const viewDayBtn = document.getElementById('viewDayBtn');
    const postModal = document.getElementById('postModal');
    const closeModal = document.getElementById('closeModal');
    const modalDate = document.getElementById('modalDate');
    const modalTime = document.getElementById('modalTime');
    const modalSocialNetwork = document.getElementById('modalSocialNetwork');
    const modalText = document.getElementById('modalText');
    const modalImage = document.getElementById('modalImage');
    const editFromModal = document.getElementById('editFromModal');
    const deleteFromModal = document.getElementById('deleteFromModal');
    const editModal = document.getElementById('editModal');
    const closeEditModal = document.getElementById('closeEditModal');
    const editForm = document.getElementById('editForm');
    let lastSelectedDay = null;
    let posts = [];
    let currentEvent = null;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',  // Vista inicial con horas
        height: 'auto',
        locale: 'es',
        events: fetchPosts,
        slotMinTime: '00:00:00',  // Horario mínimo
        slotMaxTime: '24:00:00',  // Horario máximo
        allDaySlot: false,  // No mostrar la franja de "Todo el día"
        eventDurationEditable: false,  // No permitir redimensionar eventos
        eventStartEditable: false,  // No permitir arrastrar eventos
        dateClick: function(info) {
            if (lastSelectedDay) {
                lastSelectedDay.classList.remove('selected-day');
            }
            const dayEl = info.dayEl;
            if (info.view.type === 'dayGridMonth') {
                dayEl.classList.add('selected-day');
            }
            lastSelectedDay = dayEl;
            document.getElementById('date').value = info.dateStr.split('T')[0];
            document.getElementById('time').value = info.dateStr.includes('T') ? info.dateStr.split('T')[1].substring(0, 5) : '';
        },
        eventClick: function(info) {
            currentEvent = info.event;
            modalDate.textContent = info.event.startStr.split('T')[0];
            modalTime.textContent = info.event.extendedProps.time || 'Sin hora';
            modalSocialNetwork.textContent = info.event.extendedProps.social_network;
            modalText.textContent = info.event.extendedProps.text;
            if (info.event.extendedProps.image_path) {
                modalImage.src = info.event.extendedProps.image_path;
                modalImage.style.display = 'block';
            } else {
                modalImage.style.display = 'none';
            }
            postModal.style.display = 'block';
        }
    });
    calendar.render();

    async function fetchPosts(fetchInfo, successCallback) {
        const response = await fetch('/posts');
        posts = await response.json();
        const events = posts.map(post => {
            const start = post.time ? `${post.date}T${post.time}` : post.date;
            return {
                id: post.id,
                title: `${post.social_network}: ${post.text.substring(0, 10)}...`,
                start: start,
                allDay: !post.time,
                extendedProps: {
                    time: post.time,
                    social_network: post.social_network,
                    text: post.text,
                    image_path: post.image_path
                }
            };
        });
        successCallback(events);
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('date', document.getElementById('date').value);
        formData.append('time', document.getElementById('time').value);
        formData.append('social_network', document.getElementById('socialNetwork').value);
        formData.append('text', document.getElementById('text').value);
        formData.append('image', document.getElementById('image').files[0]);

        await fetch('/posts', {
            method: 'POST',
            body: formData
        });
        calendar.refetchEvents();
        form.reset();
    });

    exportBtn.addEventListener('click', () => {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        doc.text('Plan de Publicaciones en Redes Sociales', 10, 10);
        doc.setFontSize(12);
        posts.sort((a, b) => new Date(`${a.date} ${a.time || '00:00'}`) - new Date(`${b.date} ${b.time || '00:00'}`));
        let y = 20;
        posts.forEach((post, index) => {
            const textLines = doc.splitTextToSize(`${index + 1}. ${post.date} ${post.time || ''} - ${post.social_network}: ${post.text}${post.image_path ? ' [Con imagen]' : ''}`, 180);
            doc.text(textLines, 10, y);
            y += textLines.length * 7;
            if (y > 280) {
                doc.addPage();
                y = 10;
            }
        });
        doc.save('plan_publicaciones.pdf');
    });

    viewMonthBtn.addEventListener('click', () => {
        calendar.changeView('dayGridMonth');
    });

    viewWeekBtn.addEventListener('click', () => {
        calendar.changeView('timeGridWeek');
    });

    viewDayBtn.addEventListener('click', () => {
        calendar.changeView('timeGridDay');
    });

    closeModal.addEventListener('click', () => {
        postModal.style.display = 'none';
    });

    deleteFromModal.addEventListener('click', async () => {
        if (currentEvent) {
            await fetch(`/posts/${currentEvent.id}`, { method: 'DELETE' });
            currentEvent.remove();
            postModal.style.display = 'none';
        }
    });

    editFromModal.addEventListener('click', () => {
        if (currentEvent) {
            const eventData = currentEvent.extendedProps;
            document.getElementById('editDate').value = currentEvent.startStr.split('T')[0];
            document.getElementById('editTime').value = eventData.time || '';
            document.getElementById('editSocialNetwork').value = eventData.social_network;
            document.getElementById('editText').value = eventData.text;
            document.getElementById('existingImagePath').value = eventData.image_path || '';
            editModal.style.display = 'block';
            postModal.style.display = 'none';
        }
    });

    closeEditModal.addEventListener('click', () => {
        editModal.style.display = 'none';
    });

    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (currentEvent) {
            const formData = new FormData();
            formData.append('date', document.getElementById('editDate').value);
            formData.append('time', document.getElementById('editTime').value);
            formData.append('social_network', document.getElementById('editSocialNetwork').value);
            formData.append('text', document.getElementById('editText').value);
            formData.append('existing_image_path', document.getElementById('existingImagePath').value);
            formData.append('image', document.getElementById('editImage').files[0]);

            await fetch(`/posts/${currentEvent.id}`, {
                method: 'PUT',
                body: formData
            });
            calendar.refetchEvents();
            editModal.style.display = 'none';
        }
    });

    // Activar el clic en los botones de subir imagen
    document.querySelectorAll('.upload-btn-wrapper .btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.nextElementSibling; // El input es el siguiente elemento
            if (input && input.type === 'file') {
                input.click();
            }
        });
    });

    // Filtro de texto para Twitter/X (280 caracteres)
    const socialNetworkSelect = document.getElementById('socialNetwork');
    const textArea = document.getElementById('text');
    const twitterCharLimit = 280;

    function applyTwitterCharLimit() {
        const selectedSocialNetwork = socialNetworkSelect.value;
        if (selectedSocialNetwork === 'Twitter/X') {
            textArea.setAttribute('maxlength', twitterCharLimit);
            // Mostrar conteo de caracteres
            let charCount = textArea.value.length;
            if (charCount > twitterCharLimit) {
                textArea.value = textArea.value.substring(0, twitterCharLimit);
                charCount = twitterCharLimit;
            }
            textArea.setAttribute('placeholder', `Máximo ${twitterCharLimit} caracteres (quedan ${twitterCharLimit - charCount})`);
        } else {
            textArea.removeAttribute('maxlength');
            textArea.setAttribute('placeholder', '');
        }
    }

    // Aplicar el filtro al cargar la página
    applyTwitterCharLimit();

    // Escuchar cambios en la selección de red social
    socialNetworkSelect.addEventListener('change', applyTwitterCharLimit);

    // Actualizar el conteo de caracteres mientras se escribe
    textArea.addEventListener('input', () => {
        const selectedSocialNetwork = socialNetworkSelect.value;
        if (selectedSocialNetwork === 'Twitter/X') {
            let charCount = textArea.value.length;
            if (charCount > twitterCharLimit) {
                textArea.value = textArea.value.substring(0, twitterCharLimit);
                charCount = twitterCharLimit;
            }
            textArea.setAttribute('placeholder', `Máximo ${twitterCharLimit} caracteres (quedan ${twitterCharLimit - charCount})`);
        }
    });
    // Filtro de texto para Twitter/X en el modal de edición
    const editSocialNetworkSelect = document.getElementById('editSocialNetwork');
    const editTextArea = document.getElementById('editText');

    function applyTwitterCharLimitEdit() {
        const selectedSocialNetwork = editSocialNetworkSelect.value;
        if (selectedSocialNetwork === 'Twitter/X') {
            editTextArea.setAttribute('maxlength', twitterCharLimit);
            let charCount = editTextArea.value.length;
            if (charCount > twitterCharLimit) {
                editTextArea.value = editTextArea.value.substring(0, twitterCharLimit);
                charCount = twitterCharLimit;
            }
            editTextArea.setAttribute('placeholder', `Máximo ${twitterCharLimit} caracteres (quedan ${twitterCharLimit - charCount})`);
        } else {
            editTextArea.removeAttribute('maxlength');
            editTextArea.setAttribute('placeholder', '');
        }
    }

    // Aplicar el filtro al abrir el modal de edición
    editFromModal.addEventListener('click', () => {
        if (currentEvent) {
            const eventData = currentEvent.extendedProps;
            document.getElementById('editDate').value = currentEvent.startStr.split('T')[0];
            document.getElementById('editTime').value = eventData.time || '';
            document.getElementById('editSocialNetwork').value = eventData.social_network;
            document.getElementById('editText').value = eventData.text;
            document.getElementById('existingImagePath').value = eventData.image_path || '';
            editModal.style.display = 'block';
            postModal.style.display = 'none';
            applyTwitterCharLimitEdit(); // Aplicar el filtro al abrir el modal
        }
    });

    // Escuchar cambios en la selección de red social en el modal de edición
    editSocialNetworkSelect.addEventListener('change', applyTwitterCharLimitEdit);

    // Actualizar el conteo de caracteres mientras se escribe en el modal de edición
    editTextArea.addEventListener('input', () => {
        const selectedSocialNetwork = editSocialNetworkSelect.value;
        if (selectedSocialNetwork === 'Twitter/X') {
            let charCount = editTextArea.value.length;
            if (charCount > twitterCharLimit) {
                editTextArea.value = editTextArea.value.substring(0, twitterCharLimit);
                charCount = twitterCharLimit;
            }
            editTextArea.setAttribute('placeholder', `Máximo ${twitterCharLimit} caracteres (quedan ${twitterCharLimit - charCount})`);
        }
    });
});