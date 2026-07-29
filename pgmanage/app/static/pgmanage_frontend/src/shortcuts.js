/*
This file is part of OmniDB.
OmniDB is open-source software, distributed "AS IS" under the MIT license in the hope that it will be useful.

The MIT License (MIT)

Portions Copyright (c) 2015-2020, The OmniDB Team
Portions Copyright (c) 2017-2020, 2ndQuadrant Limited

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

let default_shortcuts = {
  'shortcut_run_query': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'Q',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'Q',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'Q',
    }
  },
  'shortcut_run_selection': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'R',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'R',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'R',
    }
  },
  'shortcut_cancel_query': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'C',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'C',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'C',
    }
  },
  'shortcut_indent': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'S',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'S',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'S',
    }
  },
  'shortcut_find_replace': {
    'windows': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'F',
    },
    'linux': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'F',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'F',
    }
  },
  'shortcut_new_inner_tab': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'I',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'I',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'I',
    }
  },
  'shortcut_remove_inner_tab': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': true,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'Q',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': true,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'Q',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': true,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'Q',
    }
  },
  'shortcut_left_inner_tab': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'O',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'O',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'O',
    }
  },
  'shortcut_right_inner_tab': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'P',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'P',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'P',
    }
  },
  'shortcut_autocomplete': {
    'windows': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'SPACE',
    },
    'linux': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'SPACE',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'A',
    }
  },
  'shortcut_explain': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'W',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'W',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'W',
    }
  },
  'shortcut_explain_analyze': {
    'windows': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'E',
    },
    'linux': {
        'ctrl_pressed': false,
        'shift_pressed': false,
        'alt_pressed': true,
        'meta_pressed': false,
        'shortcut_key': 'E',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'E',
    }
  },
  'shortcut_quick_search': {
    'windows': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'P',
    },
    'linux': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'P',
    },
    'macos': {
        'ctrl_pressed': true,
        'shift_pressed': false,
        'alt_pressed': false,
        'meta_pressed': false,
        'shortcut_key': 'P',
    }
  },
  'shortcut_focus_database_tree': {
    'windows': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '0',
    },
    'linux': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '0',
    },
    'macos': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '0',
    }
  },
  'shortcut_focus_selected_tab': {
    'windows': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '1',
    },
    'linux': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '1',
    },
    'macos': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '1',
    }
  },
  'shortcut_focus_data_grid': {
    'windows': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '2',
    },
    'linux': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '2',
    },
    'macos': {
      'ctrl_pressed': true,
      'shift_pressed': false,
      'alt_pressed': false,
      'meta_pressed': false,
      'shortcut_key': '2',
    }
  },
}

export { default_shortcuts }
