ace.define("ace/theme/omnidb",["require","exports","module","ace/lib/dom"], function(require, exports, module) {

exports.isDark = false;
exports.cssClass = "ace-omnidb";
exports.cssText = ".ace-omnidb {\
background-color: #FFFFFF;\
font-size: 1em;\
}\
.ace-omnidb .ace_print-margin {\
width: 1px;\
background: #f6f6f6\
}\
.ace-omnidb .ace_cursor {\
color: #206bc4;\
opacity: 0.5\
}\
.ace-omnidb .ace_marker-layer .ace_selection {\
background: rgba(21, 97, 172, 0.2);\
}\
.ace-omnidb.ace_multiselect .ace_selection.ace_start {\
box-shadow: 0 0 3px 0px #FFFFFF;\
}\
.ace-omnidb .ace_marker-layer .ace_step {\
background: rgb(255, 255, 0)\
}\
.ace-omnidb .ace_marker-layer .ace_bracket {\
margin: 0 0 0 -1px;\
border: 1px solid rgb(245,159,0);\
background-color: rgba(245,159,0, 0.5);\
}\
.ace-omnidb .ace_marker-layer .ace_active-line {\
background: #e9f0f9\
}\
.ace-omnidb .ace_gutter-active-line {\
background-color: #e9f0f9\
}\
.ace-omnidb .ace_gutter-cell.ace_error {\
background:url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 51.976 51.976'%3e %3ccircle style='fill:white' cx='25.75' cy='25.75' r='15.160686' /%3e %3cpath fill='%23D72239' d='M44.373 7.603c-10.137-10.137-26.632-10.138-36.77 0-10.138 10.138-10.137 26.632 0 36.77s26.632 10.138 36.77 0c10.137-10.138 10.137-26.633 0-36.77zm-8.132 28.638a2 2 0 01-2.828 0l-7.425-7.425-7.778 7.778a2 2 0 11-2.828-2.828l7.778-7.778-7.425-7.425a2 2 0 112.828-2.828l7.425 7.425 7.071-7.071a2 2 0 112.828 2.828l-7.071 7.071 7.425 7.425a2 2 0 010 2.828z'/%3e %3c/svg%3e\") no-repeat 4px/0.775rem\
}\
.ace-omnidb .ace_invisible {\
color: #D1D1D1\
}\
.ace-omnidb .ace_keyword,\
.ace-omnidb .ace_meta,\
.ace-omnidb .ace_storage,\
.ace-omnidb .ace_storage.ace_type,\
.ace-omnidb .ace_support.ace_type {\
color: #206bc4;\
}\
.ace-omnidb .ace_storage,\
.ace-omnidb .ace_storage.ace_type,\
.ace-omnidb .ace_support.ace_type {\
color: #206bc4;\
font-weight: 700;\
}\
.ace-omnidb .ace_keyword.ace_operator {\
color: #667382\
}\
.ace-omnidb .ace_constant.ace_character,\
.ace-omnidb .ace_constant.ace_language,\
.ace-omnidb .ace_constant.ace_numeric,\
.ace-omnidb .ace_keyword.ace_other.ace_unit,\
.ace-omnidb .ace_support.ace_constant,\
.ace-omnidb .ace_variable.ace_parameter {\
color: #d6336c\
}\
.ace-omnidb .ace_constant.ace_other {\
color: #666969\
}\
.ace-omnidb .ace_invalid {\
color: #FFFFFF;\
background-color: #C82829\
}\
.ace-omnidb .ace_invalid.ace_deprecated {\
color: #FFFFFF;\
background-color: #8959A8\
}\
.ace-omnidb .ace_fold {\
background-color: #4271AE;\
border-color: #4D4D4C\
}\
.ace-omnidb .ace_entity.ace_name.ace_function,\
.ace-omnidb .ace_support.ace_function,\
.ace-omnidb .ace_variable {\
color: #ae3ec9\
}\
.ace-omnidb .ace_support.ace_class,\
.ace-omnidb .ace_support.ace_type {\
color: #C99E00\
}\
.ace-omnidb .ace_heading,\
.ace-omnidb .ace_markup.ace_heading,\
.ace-omnidb .ace_string {\
color: #0ca678\
}\
.ace-omnidb .ace_entity.ace_name.ace_tag,\
.ace-omnidb .ace_entity.ace_other.ace_attribute-name,\
.ace-omnidb .ace_meta.ace_tag,\
.ace-omnidb .ace_string.ace_regexp,\
.ace-omnidb .ace_variable {\
color: #0ca678\
}\
.ace-omnidb .ace_comment {\
color: #767f8f\
}\
.ace-omnidb .ace_indent-guide {\
background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAE0lEQVQImWP4////f4bdu3f/BwAlfgctduB85QAAAABJRU5ErkJggg==) right repeat-y\
}\
.ace-omnidb .ace_folding-enabled > .ace_gutter-cell {\
    color: #206bc4;\
}\
.ace-omnidb .ace_search.right {\
display: flex;\
flex-direction: column;\
align-items: stretch;\
background-color: #E8EFF8;\
border: 1px solid #CAD0D8 !important;\
padding: 8px 24px 8px 8px;\
right: 6px;\
top: 3px;\
font-family: 'Poppins', sans-serif;\
font-size: 0.75rem;\
border-radius: 6px;\
border-right: initial;\
}\
.ace-omnidb .ace_search_form, .ace-omnidb .ace_replace_form {\
display: flex;\
margin-bottom: 16px;\
margin-right: 0 !important;\
position: relative;\
overflow: visible;\
width: 385px;\
}\
.ace-omnidb .ace_search_form.ace_nomatch, .ace_search_form.ace_nomatch > .ace_search_field {\
outline: 0;\
}\
.ace_search_form.ace_nomatch:after {\
content: 'No matches';\
color: #D72239;\
display: block;\
position: absolute;\
left: 0.75rem;\
bottom: 0;\
transform: translateY(100%);\
font-size: 0.6rem;\
font-weight: 500;\
}\
.ace-omnidb .ace_replace_form {\
margin-right: 20px;\
}\
.ace-omnidb .ace_search_field {\
background-color: #FFFFFF;\
border: 1px solid #CAD0D8;\
color: #16171E;\
border-radius: 6px 0 0 6px;\
border-right: 0;\
width: 70%;\
padding: 0.375rem 0.75rem;\
height: calc(1.5em + 0.75rem + 2px);\
box-sizing: border-box;\
}\
.ace-omnidb .ace_searchbtn {\
display: flex;\
align-items: center;\
justify-content: center;\
flex: 1 1 2.2rem;\
padding: 0.375rem 0.75rem;\
height: calc(1.5em + 0.75rem + 2px);\
flex-shrink: 0;\
box-sizing: border-box;\
border-color: #CAD0D8;\
color: #747D8D;\
font-weight: 500;\
}\
.ace-omnidb .ace_searchbtn.prev, .ace-omnidb .ace_searchbtn.next {\
padding: 0.375rem 0.75rem;\
}\
.ace-omnidb .ace_searchbtn.prev:after, .ace-omnidb .ace_searchbtn.next:after {\
border-color: #747D8D;\
}\
.ace-omnidb .ace_searchbtn:last-child {\
border-radius: 0 6px 6px 0;\
}\
.ace-omnidb .ace_searchbtn_close {\
width: 16px;\
height: 16px;\
background-size: cover;\
top: 5px;\
right: 5px;\
}\
.ace-omnidb .ace_searchbtn_close:hover {\
background-color: #1560AD;\
}\
.ace-omnidb .ace_search_options {\
margin-bottom: 0;\
}\
.ace-omnidb .ace_search_options .ace_button {\
color: #16171E;\
padding: 0.2rem;\
min-width: 1.25rem;\
height: 1.3rem;\
display: inline-block;\
text-align: center;\
border-radius: 6px;\
background-color: #fff;\
border: 0;\
margin-left: 6px;\
}\
.ace-omnidb .ace_search_options .ace_button.checked {\
background-color: #1560AD;\
color: #F8FAFD;\
}\
.ace-omnidb .ace_search_options .ace_button[action='toggleReplace'] {\
padding: 0.25rem !important;\
margin-top: 0 !important;\
}\
.ace-omnidb .ace_search_options .ace_search_counter {\
padding-top: 5px;\
font-family: inherit;\
}\
.ace-omnidb.ace_autocomplete {\
border: 1px solid #CAD0D8 !important;\
border-radius: 6px !important;\
box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;\
}\
.ace-omnidb.ace_autocomplete .ace_marker-layer .ace_active-line {\
background-color: #e9f0f9 !important;\
}\
.ace-omnidb.ace_autocomplete .ace_marker-layer .ace_line-hover {\
background-color: rgba(21, 96, 173, 0.15) !important;\
border: 0 !important;\
}\
.ace-omnidb .ace_completion-meta {\
font-style: italic;\
}\
.ace-omnidb .ace_tooltip {\
border-radius: 6px;\
padding: 8px;\
box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);\
background-color: #C6DAF3;\
color: #16171E;\
border: 0;\
}\
.ace-omnidb .ace_icon.ace_error {\
background:url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 51.976 51.976'%3e %3ccircle style='fill:white' cx='25.75' cy='25.75' r='15.160686' /%3e %3cpath fill='%23D72239' d='M44.373 7.603c-10.137-10.137-26.632-10.138-36.77 0-10.138 10.138-10.137 26.632 0 36.77s26.632 10.138 36.77 0c10.137-10.138 10.137-26.633 0-36.77zm-8.132 28.638a2 2 0 01-2.828 0l-7.425-7.425-7.778 7.778a2 2 0 11-2.828-2.828l7.778-7.778-7.425-7.425a2 2 0 112.828-2.828l7.425 7.425 7.071-7.071a2 2 0 112.828 2.828l-7.071 7.071 7.425 7.425a2 2 0 010 2.828z'/%3e %3c/svg%3e\") no-repeat 4px/0.775rem\
}\
.ace-omnidb .ace_url {\
color: #767f8f;\
}\
.ace-omnidb .ace_link_marker {\
position: absolute;\
border-radius: 0px;\
border-bottom: 2px solid #1560AD;\
}\
";

var dom = require("../lib/dom");
dom.importCssString(exports.cssText, exports.cssClass);
});
