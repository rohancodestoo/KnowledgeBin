document.addEventListener('DOMContentLoaded', ()=> {
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const pinboard = document.getElementById('pinboard');
  const noteForm = document.getElementById('new-note-form');

  // --- Helper Functions to initialize Note behavior ---
  
  const initDelete = (btn) => {
    btn.addEventListener('click', async (ev)=>{
      const id = btn.dataset.id;
      if(!confirm('Delete note?')) return;
      
      const res = await fetch('/notes/delete/'+id+'/', {method:'POST', headers:{'X-CSRFToken':csrftoken}});
      const json = await res.json();
      
      if(json.success) {
        // Find and remove the note element from the DOM with a fade-out animation
        const noteToRemove = document.querySelector(`.note[data-id="${id}"]`);
        if (noteToRemove) {
          noteToRemove.style.opacity = '0';
          noteToRemove.style.transform = 'scale(0.8)';
          
          setTimeout(() => {
            noteToRemove.remove();
            // Show "No notes yet" message if the last note was deleted
            if (!pinboard.querySelector('.note')) {
              pinboard.innerHTML = '<p class="no-notes-message">No notes yet — create one!</p>';
            }
          }, 300);
        }
      } else {
        alert('Failed to delete note.');
      }
    });
  }

  const initDrag = (n) => {
    n.addEventListener('mousedown', (ev)=>{
      // Only start drag if not clicking on a control element
      if (ev.target.classList.contains('delete-note')) return;

      dragged = n;
      offsetX = ev.offsetX; offsetY = ev.offsetY;
      n.style.cursor = 'grabbing';
      n.style.zIndex = 9999;
    });
  };

  // --- Global Dragging Logic ---
  let dragged = null, offsetX=0, offsetY=0;

  // Initialize drag and delete for all existing notes
  document.querySelectorAll('.note').forEach(initDrag);
  document.querySelectorAll('.delete-note').forEach(initDelete);

  document.addEventListener('mousemove', (ev)=>{
    if(!dragged) return;
    // Calculate position relative to the pinboard, not the window
    dragged.style.left = (ev.clientX - pinboard.getBoundingClientRect().left - offsetX) + 'px';
    dragged.style.top = (ev.clientY - pinboard.getBoundingClientRect().top - offsetY) + 'px';
  });

  document.addEventListener('mouseup', async (ev)=>{
    if(!dragged) return;
    
    dragged.style.cursor = 'grab';
    const id = dragged.dataset.id;
    const x = Math.max(0, parseInt(dragged.style.left.replace('px', '')));
    const y = Math.max(0, parseInt(dragged.style.top.replace('px', '')));
    const z = parseInt(dragged.style.zIndex) || 1;
    
    // Reset z-index after drag
    dragged.style.zIndex = 1;

    // Send update to server
    const params = new URLSearchParams({x,y,z});
    await fetch('/notes/update/'+id+'/', {method:'POST', headers:{'X-CSRFToken':csrftoken}, body:params});
    
    dragged = null;
  });
  
  // --- Create Note Logic (Optimized) ---
  document.getElementById('create-note').addEventListener('click', async (e)=>{
    e.preventDefault();
    const data = new FormData(noteForm);
    
    // Clear form fields immediately for better UX
    const newTitle = data.get('title');
    const newContent = data.get('content');
    const newColor = data.get('color');

    noteForm.elements['title'].value = '';
    noteForm.elements['content'].value = '';
    // Preserve color for next note

    const res = await fetch('/notes/create/', {method:'POST', headers:{'X-CSRFToken':csrftoken}, body:data});
    const json = await res.json();
    
    if(json.success) {
      // Dynamic DOM insertion instead of location.reload()
      const noteHtml = `
        <div class="note new-note-fade-in" data-id="${json.id}" style="left: 50px; top: 50px; background: ${newColor}; z-index: 1">
          <div class="note-header">
            <strong>${newTitle || 'Untitled'}</strong>
            <button class="delete-note" data-id="${json.id}">✕</button>
          </div>
          <div class="note-body">${newContent || '...'}</div>
        </div>
      `;
      pinboard.insertAdjacentHTML('afterbegin', noteHtml);

      // Re-initialize drag and delete listeners for the new note
      const newNote = pinboard.querySelector(`[data-id="${json.id}"]`);
      if (newNote) {
        initDrag(newNote);
        initDelete(newNote.querySelector('.delete-note'));
        
        // Remove the animation class after the transition ends
        setTimeout(() => newNote.classList.remove('new-note-fade-in'), 300); 
      }
      
      // Remove "No notes yet" message if it exists
      pinboard.querySelector('.no-notes-message')?.remove();
      
    } else {
      alert('Failed to create note. Please check your input.');
    }
  });
});