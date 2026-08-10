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

import { emitter } from "./emitter";
import { tabsStore } from "./stores/stores_initializer";
import { Modal } from "bootstrap";
import { createOmnisUiAssistant } from "./omnis-control";

function startTutorial(p_tutorial_name) {
  if (v_omnis.omnis_ui_assistant) {
    v_omnis.omnis_ui_assistant.self_destruct();
  }
  // workaround to prevent ability to scroll the app UI while side-panel "waves" are shown
  $('body').css('overflow','hidden');
  // Disabling interactions with omnis.
  v_omnis.div.classList.add('omnis--active');
  // Instantiate the component.
  v_omnis.omnis_ui_assistant = createOmnisUiAssistant({
    p_callback_end: function(){
      // Configuring to delete the componente when it's no longer used.
      delete v_omnis.omnis_ui_assistant;
      // Enabling interactions with omnis.
      v_omnis.div.classList.remove('omnis--active');
      emitter.emit('omnisVisibilityChanged');
    },
    // Omnis Object
    p_omnis: v_omnis
  });
  emitter.emit('omnisVisibilityChanged');
  // Setting the tutorial to the default example tutorial `main`.
  var v_tutorial_name = (p_tutorial_name) ? p_tutorial_name : 'main';
  var v_button_inner_query_attr = ' disabled title="Open a new connection first." ';
  if (!!tabsStore.selectedPrimaryTab?.metaData?.secondaryTabs?.length) {
      v_button_inner_query_attr = '';
  }
  var v_button_inner_query =
  '<li class="mb-2">' +
    `<button id="connection_tab_tutorial" ` + v_button_inner_query_attr + ` type="button" class="btn btn-primary d-flex align-items-center">` +
      '<i class="fas fa-list me-2"></i>The Connection Tab' +
    '</button>' +
  '</li>';
  // Configuring the available tutorials.
  var v_tutorials = {
    'main': [
      {
        p_message: 'This contains the outer connection and global panels [ connections_list_manager, snippets_panel, [conn_1, conn_2, ...], add_connection]',
        p_target: document.getElementsByClassName('omnidb__tab-menu omnidb__tab-menu--primary')[0],
        p_title: 'Primary menu'
      },
      {
        p_message: 'This contains general settings and options, such as [ versioning, connections_list_manager, user_setting, plugins...]',
        p_target: document.getElementsByClassName('omnidb__utilities-menu')[0],
        p_title: 'Utilities menu'
      }
    ],
    'utilities_menu': [
      {
        p_callback_end: function() {$('.omnidb__utilities-menu').removeClass('omnidb__utilities-menu--show');},
        p_callback_start: function() {$('.omnidb__utilities-menu').addClass('omnidb__utilities-menu--show');},
        p_clone_target: true,
        p_message: `
        <p>Contains general settings and options:</p>
        <ul>
        <li>Username and versioning.</li>
        <li><i class="fas fa-user omnidb__theme__text--primary me-2"></i>User management.</li>
        <li><i class="fas fa-cog omnidb__theme__text--primary me-2"></i>UI settings (shortcuts, theme, fonts...).</li>
        <li><i class="fas fa-info-circle omnidb__theme__text--primary me-2"></i>About.</li>
        <li><i class="fas fa-sign-out-alt omnidb__theme__text--primary me-2"></i>Sign Out.</li>
        </ul>
        `,
        p_target: document.getElementsByClassName('omnidb__utilities-menu')[0],
        p_title: 'Utilities Menu',
        p_update_delay: 350
      },
      {
        p_callback_end: function() {$('.omnidb__utilities-menu').removeClass('omnidb__utilities-menu--show');},
        p_callback_start: function() {$('.omnidb__utilities-menu').addClass('omnidb__utilities-menu--show');},
        p_callback_after_update_start: function() {setTimeout(function(){
            if (v_omnis.omnis_ui_assistant.divClonedElement.children[0]) {
              v_omnis.omnis_ui_assistant.divClonedElement.children[0].style.width='';
            }
          },50);
        },
        p_clone_target: true,
        p_message: `
        <p>If you just configured Pgmanage and logged with the default <strong>admin</strong> user, you should create the first user.</p>
        <p>Follow this walkthrough if you want to create other users as well.</p>
        `,
        p_next_button: true,
        p_target: document.getElementById('utilities-menu__link-user'),
        p_title: 'Managing Users'
      },
      {
        p_callback_start: function() { document.getElementById('utilities-menu__link-user').click();},
        p_callback_after_update_start: function() {setTimeout(function(){
            if (v_omnis.omnis_ui_assistant.divClonedElement.children[0]) {
              v_omnis.omnis_ui_assistant.divClonedElement.children[0].classList.remove('ms-2');
            }
          },50);
        },
        p_clone_target: true,
        p_message: `
        <p>Click on <strong>Add new user</strong>.</p>
        `,
        p_next_button: false,
        p_target: function() {var v_target = document.getElementById('add_new_user_button'); return v_target},
        p_title: 'Add a New User',
        p_update_delay: 1000
      },
      {
        p_callback_start: function() { document.getElementById('add_new_user_button').click() },
        p_message: `
        <ul>
        <li><i class="fas fa-user omnidb__theme__text--primary me-2"></i>PgManage login name.</li>
        <li><i class="fas fa-key omnidb__theme__text--primary me-2"></i>PgManage login password.</li>
        </ul>
        `,
        p_target: function() {var v_target = document.getElementsByClassName("modal-users__form")[0]; return v_target},
        p_title: 'User Options',
        p_update_delay: 350
      }
    ],
    'connections_menu': [
      {
        p_clone_target: true,
        p_message: `
        <p>This is the outer connections menu. Each connection added becomes a new item in this menu.</p>
        <p>The menu initially contains.</p>
        <ul>
        <li>Connections manager.</li>
        <li>Welcome, tutorial and useful links.</li>
        <li>Snippets panel toggler.</li>
        </ul>
        <p>Let's first <span class="badge bg-info">add a new connection</span>.</p>
        <p>Please, click on the <i class="fas fa-bolt"></i> button.</p>
        `,
        p_target: document.querySelectorAll('.omnidb__tab-menu--primary .omnidb__tab-menu__link .omnidb__tab-menu__link-icon')[0],
        p_title: 'Primary menu'
      },
      {
        p_callback_start: function() {
          Modal.getOrCreateInstance("#connections-modal").show()
          setTimeout(function() {
            document.getElementById('add_connection_button').click()
          }, 100)
        },
        p_callback_after_update_start: function() {
          setTimeout(function() {
            v_omnis.omnis_ui_assistant.divClonedElement.firstChild.style.transform = ''
          }, 100)
        },
        p_message: `
        <p>Click on <strong> Connection <strong></p>
        `,
        p_clone_target: true,
        p_target: function() {var v_target = document.getElementById('add_connection_dropdown_menu'); return v_target},
        p_title: 'Add a New Connection',
        p_update_delay: 1000,
        p_next_button: false,
      },
      {
        p_callback_start: function() {
          document.getElementById('add_connection_dropdown_item').click()
        },
        p_message: `
        <p>Select the proper DBMS technology.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionType'); return v_target},
        p_title: 'Connection Type',
        p_update_delay: 300
      },
      {
        p_message: `
        <p>Type a helpful name for the connection.</p>
        <p>This is used as name reference on many UI areas.</p>
        <p>i.e: Local dvdrental barman.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionName'); return v_target},
        p_title: 'Title'
      },
      {
        p_message: `
        <p>Type the server address. Do not include ports.</p>
        <p>i.e:127.0.0.1</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionServer'); return v_target},
        p_title: 'Server'
      },
      {
        p_message: `
        <p>Type the port of the server.</p>
        <p>i.e: PostgreSQL uses 5432 by default.<br>If you are using pgbouncer, you may want to use 6432 as the entry point.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionPort'); return v_target},
        p_title: 'Port'
      },
      {
        p_message: `
        <p>Type the name of the database.</p>
        <p>i.e: postgres, dvdrental.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionDatabase'); return v_target},
        p_title: 'Database'
      },
      {
        p_message: `
        <p>Type the name of the user with privileges to access the database.</p>
        <p>i.e: postgres.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionUsername'); return v_target},
        p_title: 'User'
      },
      {
        p_message: `
        <p>This is <strong>optional</strong>.</p>
        <p>If you don't save the user password, you will be required to manually input it everytime a new connection to this database is started.</p>
        <p>If saved, this password will be stored in the application database.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionPassword'); return v_target},
        p_title: 'User password'
      },
      {
        p_message: `
        <p>You may want to hit 'Test' before saving the connection.</p>
        <p>After that, click <strong>Save changes</strong>.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionTestButton'); return v_target},
        p_title: 'Test the Connection'
      }
    ],
    'terminal_connection': [
      {
        p_clone_target: true,
        p_message: `
        <p>First let's open the <strong>connections manager</strong> interface.</p>
        `,
        p_target: document.querySelector('.omnidb__tab-menu--primary .omnidb__tab-menu__link .omnidb__tab-menu__link-icon'),
        p_title: 'Accessing connections manager'
      },
      {
        // p_callback_after_update_start: function() {setTimeout(function(){var v_target = document.getElementById('button_new_connection'); v_omnis.omnis_ui_assistant.divClonedElement.children[0].classList.remove('ml-2');},50);},
        p_callback_start: function() {
          Modal.getOrCreateInstance("#connections-modal").show()
          setTimeout(function() {
            document.getElementById('add_connection_button').click()
          }, 100)
        },
        p_callback_after_update_start: function() {
          setTimeout(function() {
            v_omnis.omnis_ui_assistant.divClonedElement.firstChild.style.transform = ''
          }, 100)
        },
        p_clone_target: true,
        p_message: `
        <p>Click on <strong> Connection <strong></p>
        `,
        p_next_button: false,
        p_target: function() {var v_target = document.getElementById('add_connection_dropdown_menu'); return v_target},
        p_title: 'Add a New Connection',
        p_update_delay: 1000
      },
      {
        p_callback_start: function() {
          document.getElementById('add_connection_dropdown_item').click()
        },
        p_message: `
        <p>Select the Terminal technology.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionType'); return v_target},
        p_title: 'Connection Type',
        p_update_delay: 300
      },
      {
        p_callback_start: function() {
          document.getElementById('connectionName').focus()
        },
        p_message: `
        <p>Type a helpful name for the terminal connection.</p>
        <p>This is used as name reference on many UI areas.</p>
        <p>i.e: Local terminal.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionName'); return v_target},
        p_title: 'Title'
      },
      {
        p_callback_start: function() {
          document.getElementById('sshSettings').scrollIntoView()
        },
        p_message: `
        <p>The terminal utilizes SSH technology.</p>
        <p>As you can see, in this case SSH parameters are mandatory.</p>
        `,
        p_target: function() {var v_target = document.getElementById('sshTunel'); return v_target},
        p_title: 'SSH parameters'
      },
      {
        p_message: `
        <p>Type the ssh server address. Do not include ports.</p>
        <p>i.e:127.0.0.1</p>
        `,
        p_target: function() {var v_target = document.getElementById('sshServer'); return v_target},
        p_title: 'SSH server'
      },
      {
        p_message: `
        <p>Type the port of the SSH server.</p>
        <p>i.e: 22 is a default port for working with SSH tunnels.</p>
        `,
        p_target: function() {var v_target = document.getElementById('sshPort'); return v_target},
        p_title: 'SSH Port'
      },
      {
        p_message: `
        <p>Type the name of the SSH user.</p>
        <p>i.e: If you are on linux, your linux user is available for a local connection.</p>
        `,
        p_target: function() {var v_target = document.getElementById('sshUsername'); return v_target},
        p_title: 'SSH User'
      },
      {
        p_message: `
        <p>This is <strong>optional</strong>.</p>
        <p>If you want you can save the Passphrase of your user.</p>
        <p>* Leaving this empty will force the tool to request for your passphrase everytime you open a terminal connection.</p>
        `,
        p_target: function() {var v_target = document.getElementById('sshPassphrase'); return v_target},
        p_title: 'SSH Passphrase'
      },
      {
        p_message: `
        <p>This is <strong>optional</strong>.</p>
        <p>It allows you to configure a SSH key.</p>
        `,
        p_target: function() {var v_target = document.getElementById('sshFileLabel'); return v_target},
        p_title: 'SSH Key'
      },
      {
        p_callback_start: function() {
          document.getElementById('connectionTestButton').focus()
        },
        p_message: `
        <p>You may want to hit 'Test' before saving the connection.</p>
        <p>After that, click <strong>Save changes</strong>.</p>
        `,
        p_target: function() {var v_target = document.getElementById('connectionTestButton'); return v_target},
        p_title: 'Test the Connection'
      }
    ],
    'snippets': [
      {
        p_clone_target: true,
        p_message: `
        <p>The snippet panel is accessible globally.</p>
        <p>Please, click on the <i class="fas fa-file-code"></i> button.</p>
        `,
        p_target: document.querySelectorAll('.omnidb__tab-menu--primary .omnidb__tab-menu__link .omnidb__tab-menu__link-icon')[2],
        p_title: 'Global Snippet Panel'
      },
      {
        // p_callback_after_update_start: function() {setTimeout(function(){var v_target = document.getElementById(v_connTabControl.snippet_tag.tabControl.selectedTab.tag.editorDivId);},50);},
        p_callback_start: function() { emitter.emit("toggle_snippet_panel");},
        p_message: `
        <p>Inside this tab you can create and edit a snippet.</p>
        <p>Go ahead and try to create some simple snippet, i.e:</p>
        <code>WHERE true SELECT 1;</code>
        <p>Then experiment clicking on the <strong>Indent</strong> button below the editor, and then <strong>Next</strong>.</p>
        `,
        p_next_button: true,
        p_target: function() {var v_target = document.querySelector('.snippets__right a[draggable="false"]'); return v_target},
        p_title: 'Snippets editor',
        p_update_delay: 600
      },
      {
        p_message: `
        <p>As you can see, the identation feature automatically adjusts your code following a pattern.</p>
        <p>Now go ahead and click <strong>Save</strong>.</p>
        `,
        p_next_button: true,
        p_target: function() {var v_target =  document.querySelector('.snippets__right a[draggable="false"]'); return v_target},
        p_title: 'Indenting'
      },
      {
        p_message: `
        <p>Every snippet you save is stored under your user.</p>
        <p>The tree on the left allows you to easily access it by double-clicking on the snippet.</p>
        `,
        p_next_button: false,
        p_target: function() {var v_target = document.querySelector(".snippets-tree > .vue-power-tree-root"); return v_target},
        p_title: 'Saved Snippets',
        p_update_delay: 600
      }
    ],
    'selecting_connection': [
      {
        p_message: `
        <p>The side panel allows you to switch between open Database Sessions and access Homepage and Snippets.</p>
        <ol style="padding-left: 1.5rem;">
          <li class="mb-2">
            To access a connection, click on the <i class="fas fa-bolt"></i> button.
          </li>
          <li class="mb-2">
            Navigate to the proper connection group.
          </li>
          <li class="mb-2">
            Click on the connection item.
          </li>
        </ol>
        <p>Now you can close this walkthrough and open a new connection.</p>
        `,
        p_position: function() {var v_target = document.getElementById(tabsStore.selectedPrimaryTab.id); return {x:v_target.getBoundingClientRect().x + 40,y:v_target.getBoundingClientRect().y}},
        p_target: function(){var v_target = document.getElementById(tabsStore.selectedPrimaryTab.id); return v_target;},
        p_title: 'Selecting a Connection'
      }
    ],
    'connection_tab': [
      {
        p_message: `
        <p>This identifies the database you are connected with.</p>
        `,
        p_target: function(){var v_target = document.querySelector('div[class*="connection-details"]'); return v_target;},
        p_title: 'Current Connection'
      },
      {
        p_message: `
        <p>This tree is main your access point to this connection.</p>
        <p><strong>How-to</strong>:</p>
        <ul style="padding-left: 1.5rem;">
          <li class="mb-1">
            <strong>Double-click</strong>: expands child nodes based on the database internal structure.
          </li>
          <li class="mb-2">
            <strong>Right-click</strong>: Context menu with actions based on the node type.
          </li>
        </ul>
        `,
        p_position: function() {var v_target = document.querySelector('div.database-tree'); return { x:v_target.getBoundingClientRect().right, y:v_target.getBoundingClientRect().top }},
        p_target: function(){var v_target = document.querySelector('div.database-tree'); return v_target;},
        p_title: 'Database Tree'
      },
      {
        p_message: `
        <p>These tabs provide additional info on the node selected in the Database Object Tree.</p>
        <p>Keep in mind that every node interaction that returns this type of info needs to query for consistency.</p>
        <p>To minimize queries, these only run when one of these tabs is visible.</p>
        <p><strong>Recommendation</strong>: Only open the property/ddl when you need to update this info.</p>
        `,
        p_target: function(){var v_target = document.querySelector('div[class*="tree-tabs"]'); return v_target;},
        p_title: 'Properties / DDL'
      },
      {
        p_message: `
        <p>There are multiple types of tabs available.</p>
        <ol style="padding-left: 1.5rem;">
          <li class="mb-1">
            <strong><i class="fas fa-terminal"></i> Console Tab</strong>: Contains a psql console.
          </li>
          <li class="mb-1">
            <strong><i class="fas fa-database"></i> Query Tabs</strong>: These have SQL editors whose commands are executed on the selected database.
          </li>

        ${['oracle', 'sqlite'].includes(tabsStore.selectedPrimaryTab.metaData.selectedDBMS) ? '' : `          <li class="mb-1">
            <strong><i class="fas fa-chart-line"></i> Monitoring Dashboard</strong>: Displays various performance metrics for the current DB connection.
          </li>
          <li class="mb-1">
            <strong><i class="fas fa-tasks"></i> Backends</strong>: Displays a list of running database server backends of the current DB connection.
        </li>`}
        </ol>
        `,
        p_target: function(){var v_target = document.querySelector(`#${tabsStore.selectedPrimaryTab.id} [data-testid="add-tab-button"]`); return v_target;},
        p_title: 'Inner Tabs'
      },
      {
        p_message: `
        <p>These buttons request actions based on the SQL editor and the querying status.</p>
        <p>For example, you can <span class="bg-info rounded px-1 text-white">run</span> a query, <span class="bg-info rounded px-1 text-white">cancel</span> an ongoing query, <span class="bg-info rounded px-1 text-white">fetch more</span>, <span class="bg-info rounded px-1 text-white">fetch all</span>
         ${tabsStore.selectedPrimaryTab.metaData.selectedDBMS === 'postgresql' ? '<span class="bg-info rounded px-1 text-white">explain</span>, <span class="bg-info rounded px-1 text-white">explain analyze</span>' : ''}.</p>
        <p>If you navigate the Tree on the left to find a table and use the action <strong>Query Data</strong> from it's context menu, the editor will autofill and the run query will be issued.</p>
        `,
        p_position: function() {var v_target = document.querySelector(`#${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_content .tab-actions`); return {x:v_target?.getBoundingClientRect()?.x + 40,y:v_target?.getBoundingClientRect()?.y}},
        p_target: function(){var v_target = document.querySelector(`#${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_content .tab-actions`); return v_target;},
        p_title: 'Actions Panel'
      },
      {
        p_message: `
        <p>Query returns will fill the area below your screen, even when they return errors.</p>
        <p>After running a query, this area will contain special tabs.</p>
        <ul style="padding-left: 1.5rem;">
          <li class="mb-1">
            <strong>Data</strong>: Contains a table with query results.
          </li>
          ${tabsStore.selectedPrimaryTab.metaData.selectedDBMS !== 'postgresql' ? '' : `   <li class="mb-1">
            <strong>Messages</strong>: Displays error messages.
          </li>
          <li class="mb-1">
            <strong>Explain</strong>: Contains a special component to display explain/explain analyze results.
          </li>`}
       
        </ul>
        `,
        p_position: function() {
          let v_target = document.querySelector(`#${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_content .result-div`);
          if (!v_target) {
            v_target = document.querySelector(`#${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_content .ace-editor`);
          }
          return {x:v_target?.getBoundingClientRect()?.x + 200,y:v_target?.getBoundingClientRect()?.y + 40}},
        p_target: function(){var v_target = document.querySelector(`#${tabsStore.selectedPrimaryTab.metaData.selectedTab.id}_content .tab-actions`); return v_target;},
        p_title: 'Query Result'
      }
    ]
  }
  // Configuring tutorial getting started, changes based on gv_desktopMode
  
  let v_tutorial_link_creating_user = !gv_desktopMode && v_super_user && __VITE_ENTERPRISE__
  ? `
  <li class="mb-2">
    <button id="utilities_menu_tutorial" type="button" class="btn btn-primary d-flex align-items-center">
      <i class="fas fa-user-plus me-2"></i>Create an pgmanage user
    </button>
  </li>`
  : ''
  v_tutorials.getting_started = [
    {
      p_message:
      '<ol class="ms-2" style="padding-left: 1.5rem;">' +
        v_tutorial_link_creating_user +
        `
        <li class="mb-2">
          <button id="connections_menu_tutorial" type="button" class="btn btn-primary d-flex align-items-center">
            <i class="fas fa-plus me-2"></i>Create a database connection
          </button>
        </li>
        <li class="mb-2">
          <button id="terminal_connection_tutorial" type="button" class="btn btn-primary d-flex align-items-center">
            <i class="fas fa-terminal me-2"></i>Create a terminal connection
          </button>
        </li>
        <li class="mb-2">
          <button id="snippets_tutorial" type="button" class="btn btn-primary d-flex align-items-center">
            <i class="fas fa-file-code me-2"></i>Meet the snippets panel
          </button>
        </li>
        <li class="mb-2">
          <button id="using_connection_tutorial" type="button" class="btn btn-primary d-flex align-items-center">
            <i class="fas fa-plug me-2"></i>Using a connection
          </button>
        </li>
        ` +
        v_button_inner_query +
      '</ol>',
      p_title: 'Getting started'
    }
  ];

  // Selecting a tutorial
  var v_steps = v_tutorials[v_tutorial_name];
  // Update the step list with the new walkthrough
  v_omnis.omnis_ui_assistant.updateStepList(v_steps);
  // Go to the first step of the walkthrough
  v_omnis.omnis_ui_assistant.goToStep(0);
  if (p_tutorial_name === "getting_started") {
    document.getElementById("snippets_tutorial").onclick = function() { startTutorial('snippets')}
    document.getElementById("using_connection_tutorial").onclick = function() { startTutorial('selecting_connection')}
    document.getElementById("terminal_connection_tutorial").onclick = function() { startTutorial('terminal_connection')}
    document.getElementById("connections_menu_tutorial").onclick = function() { startTutorial('connections_menu')}
    document.getElementById("connection_tab_tutorial").onclick = function() { startTutorial('connection_tab')}
    if (!gv_desktopMode && v_super_user && __VITE_ENTERPRISE__) {
      document.getElementById("utilities_menu_tutorial").onclick = function() { startTutorial('utilities_menu')}
    }
  }
}

export { startTutorial }