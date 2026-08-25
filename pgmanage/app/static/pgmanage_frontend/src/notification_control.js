import { useToast } from 'vue-toast-notification';
import { Modal } from "bootstrap";
import escape from 'lodash/escape';

let v_message_modal_animating = false;
let v_message_modal_queued = false;
let v_message_modal_queued_function = null;
let v_shown_callback = null;

$(function () {
  let messageModalEl = document.getElementById("modal_message")
  if ( messageModalEl) {
    messageModalEl.addEventListener('hide.bs.modal', function (e) {
      v_message_modal_animating = true;
    });
    messageModalEl.addEventListener('show.bs.modal', function (e) {
      v_message_modal_animating = true;
    });
    messageModalEl.addEventListener('hidden.bs.modal', function (e) {
      document.getElementById('modal_message_content').innerHTML = '';
      v_message_modal_animating = false;
      if (v_message_modal_queued == true) {
        if (v_message_modal_queued_function!=null)
          v_message_modal_queued_function();
        Modal.getInstance(messageModalEl).show()
      }
      v_message_modal_queued = false;
      v_message_modal_queued_function = null;
    });
    messageModalEl.addEventListener('shown.bs.modal', function (e) {
      v_message_modal_animating = false;
      if (v_shown_callback) {
        v_shown_callback();
        v_shown_callback = null;
      }
    });
  }
});

function showMessageModal(p_content_function, p_large) {

	var v_dialog = document.getElementById('modal_message_dialog');

	if (p_large==null || p_large==false) {
		v_dialog.classList.remove('modal-xl');
	}
	else {
		v_dialog.classList.add('modal-xl');
	}

  if (!v_message_modal_animating) {
		if (p_content_function!=null)
			p_content_function();
    Modal.getOrCreateInstance('#modal_message').show()
	}
  else {
    v_message_modal_queued = true;
		v_message_modal_queued_function = p_content_function;
	}

}

function showAlertContent(p_fill_content, p_funcYes = null, p_large = null)
{

	var v_create_content_function = function() {
	  var v_content_div = document.getElementById('modal_message_content');
	  var v_button_yes = document.getElementById('modal_message_yes');
	  var v_button_ok = document.getElementById('modal_message_ok');
	  var v_button_no = document.getElementById('modal_message_no');
	  var v_button_cancel = document.getElementById('modal_message_cancel');

	  p_fill_content(v_content_div);

		v_button_ok.onclick = function() {
	    if (p_funcYes!=null)
			  p_funcYes();
		};

	  v_button_yes.style.display = 'none';
	  v_button_ok.style.display = '';
	  v_button_no.style.display = 'none';
	  v_button_cancel.style.display = 'none';

	}


	showMessageModal(v_create_content_function, p_large);


}

function showAlertText(p_info, p_funcYes = null, p_large = null)
{
	showAlertContent(function(v_content_div) {
		v_content_div.textContent = p_info;
	}, p_funcYes, p_large);
}

function showAlertHtml(p_info, p_funcYes = null, p_large = null)
{
	showAlertContent(function(v_content_div) {
		v_content_div.innerHTML = p_info;
	}, p_funcYes, p_large);
}

function showConfirm(p_info,p_funcYes = null,p_funcNo = null, p_shownCallback = null, p_large = null)
{
	var v_create_content_function = function() {
	  if (p_shownCallback != null)
	    v_shown_callback = p_shownCallback;

	  var v_content_div = document.getElementById('modal_message_content');
	  var v_button_yes = document.getElementById('modal_message_yes');
	  var v_button_ok = document.getElementById('modal_message_ok');
	  var v_button_no = document.getElementById('modal_message_no');
	  var v_button_cancel = document.getElementById('modal_message_cancel');

	  v_content_div.innerHTML = p_info;

		v_button_ok.onclick = function() {
			p_funcYes();
		};

		v_button_cancel.onclick = function() {
			if (p_funcNo)
				p_funcNo();
		};

	  v_button_yes.style.display = 'none';
	  v_button_no.style.display = 'none';
	  v_button_ok.style.display = '';
	  v_button_cancel.style.display = '';
	}

	showMessageModal(v_create_content_function, p_large);

}

/**
 * Show a toast notification with a specified type and message.
 *
 * @param {string} type - The type of the toast notification.
 *                       Possible values: 'success', 'info', 'warning', 'error', 'default'
 * @param {string} message - The message to display in the toast.
 */
function showToast(type, message) {
  const titleMap = {
    'error': 'Failed',
    'success': 'Success',
    'info': 'Information',
    'default': 'Done'
  };

  let title = titleMap[type] || titleMap['default']
  let scrollableClass = type === 'error' ? 'v-toast-scrollable' : ''
  let message_lines = message.split("\n").filter(l => l.trim())
  let message_formatted = message_lines.map((line) => {return `<p>${escape(line).replace('$install_guide$', '<a target="_blank" href="https://pgmanage.readthedocs.io/en/latest/en/02_quick_start.html#install-guide">Postgresql Client Installation</a>')}</p>`}).join('')
  let html_msg = `<div class="v-toast__body p-0" >
                    <h3 class="fw-bold">${title}</h3>
                    <p class="${scrollableClass}">${message_formatted}</p>
                  </div>`
  const $toast = useToast()

  $toast.open({
    message: html_msg,
    type: type,
    duration: type === 'error' ? 30000 : 3000,
    pauseOnHover: type === 'error',
    dismissible: type !== 'error' 
  })
}

export { showAlertText, showAlertHtml, showConfirm, showToast };
