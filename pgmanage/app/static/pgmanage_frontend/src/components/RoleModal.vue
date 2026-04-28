<template>
    <div class="modal fade modal-role" id="roleModal" tabindex="-1" role="dialog" aria-hidden="true">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content modal-role__content">
          <div class="modal-header align-items-center">
            <h2 class="modal-title fw-bold">{{ modalTitle }}</h2>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>

          <div class="modal-body modal-role__body">
            <ul class="nav nav-tabs" role="tablist">
              <li class="nav-item">
                <a class="nav-link active" id="role_general-tab" data-bs-toggle="tab" href="#role_general"
                  role="tab" aria-controls="role_general" aria-selected="true">General</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" id="role_memberships-tab" data-bs-toggle="tab" href="#role_memberships" role="tab"
                  aria-controls="role_memberships" aria-selected="false">Memberships</a>
              </li>
            </ul>
            <div class="tab-content p-3 flex-grow-1">
              <!-- General tab -->
              <div class="tab-pane fade show active" id="role_general" role="tabpanel"
                  aria-labelledby="role_general-tab">
                <div class="row">
                  <!-- left col -->
                  <div class="col-6">
                    <div class="form-group mb-2">
                      <label for="role_name" class="fw-bold mb-2">Name</label>
                      <input
                        v-model="localRole.name" id="role_name" type="text"
                        :class="['form-control', { 'is-invalid': v$.localRole.name.$invalid }]">
                    </div>

                    <div class="form-group mb-2">
                      <label for="role_password" class="fw-bold mb-2">Password</label>
                      <input
                        v-model="localRole.password" id="role_password" type="password"
                        :class="['form-control', { 'is-invalid': v$.localRole.password.$invalid }]">
                    </div>

                    <div class="form-group mb-2">
                      <label for="role_valid_until" class="fw-bold mb-2">Valid Until</label>
                      <input
                        v-model="localRole.validUntil" id="role_valid_until" ref="datepicker"
                        :class="['form-control', { 'is-invalid': v$.localRole.validUntil.$invalid }]">
                    </div>

                    <div ref="daterangePicker" class="position-relative"></div>

                    <div class="form-group mb-2">
                      <label for="role_connlimit" class="fw-bold mb-2">Connection Limit</label>
                      <input
                        v-model="localRole.connectionLimit" id="role_connlimit" type="text"
                        :class="['form-control', { 'is-invalid': v$.localRole.connectionLimit.$invalid }]">
                    </div>
                  </div>

                  <!-- right col -->
                  <div class="form-group col-6 mb-2">
                    <label for="in_database" class="fw-bold mb-2">Permissions</label>
                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="roleCanLogin"
                        v-model="localRole.canLogin" >
                      <label class="form-check-label" for="roleCanLogin">
                        Can Login
                      </label>
                    </div>

                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="roleSuperuser"
                        v-model="localRole.superuser" >
                      <label class="form-check-label" for="roleSuperuser">
                        Superuser
                      </label>
                    </div>

                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="roleCanCreateUsers"
                        v-model="localRole.canCreateUsers" >
                      <label class="form-check-label" for="roleCanCreateUsers">
                        Can Create Users
                      </label>
                    </div>

                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="roleCanCreateDatabases"
                        v-model="localRole.canCreateDatabases" >
                      <label class="form-check-label" for="roleCanCreateDatabases">
                        Can Create Databases
                      </label>
                    </div>

                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="roleInherit"
                        v-model="localRole.inherit" >
                      <label class="form-check-label" for="roleInherit">
                        Inherit Permissions From Memberships
                      </label>
                    </div>

                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="roleCanReplicate"
                        v-model="localRole.canReplicate" >
                      <label class="form-check-label" for="roleCanReplicate">
                        Can Initiate Replications and Back-up
                      </label>
                    </div>

                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="roleCanBypassRLS"
                        v-model="localRole.canBypassRLS" >
                      <label class="form-check-label" for="roleCanBypassRLS">
                        Can Bypass Row-level Security Policies
                      </label>
                    </div>

                  </div>
                </div>

                <div class="form-group mb-2">
                  <PreviewBox label="Preview" :editor-text="generatedSQL" databaseTechnology="postgresql" style="height: 20vh"/>
                </div>
              </div>

              <!-- Memberships tab -->
              <div class="tab-pane fade show" id="role_memberships" role="tabpanel"
                  aria-labelledby="role_memberships-tab">
                <div>

                  <p class="fw-bold mb-0">Members:</p>

                  <div class="d-flex row fw-bold text-muted schema-editor__header">
                    <div class="col-8">
                      <p class="h6">Role Name</p>
                    </div>
                    <div class="col-3">
                      <p class="h6">Admin</p>
                    </div>
                  </div>

                  <template v-for="(member, index) in localRole.members" :key="member.index">
                    <div v-if="!member?.deleted" class="schema-editor__column d-flex row flex-nowrap form-group g-0">
                      <div class="col-8">
                        <SearchableDropdown
                          placeholder="type to search"
                          :options="existingRoleOptions"
                          :maxItem=20
                          v-model="member.name"
                        />
                      </div>
                      <div class="col-3 d-flex align-items-center">
                        <input type='checkbox' class="custom-checkbox" v-model="member.withAdmin"/>
                      </div>

                      <div :class="['col d-flex me-1', 'justify-content-end']">
                        <button @click='removeMember(localRole.members, index)' type="button"
                          class="btn btn-icon btn-icon-danger ps-2 pe-2" title="Remove">
                          <i class="fas fa-circle-xmark"></i>
                        </button>
                      </div>
                    </div>
                  </template>

                  <div class="d-flex g-0 fw-bold mt-2">
                    <button @click='addMember(localRole.members)' class="btn btn-outline-success btn-sm ms-auto">
                      Add Member
                    </button>
                  </div>

                  <p class="fw-bold mb-0">Member Of:</p>
                  <div class="d-flex row fw-bold text-muted schema-editor__header">
                    <div class="col-8">
                      <p class="h6">Role Name</p>
                    </div>
                    <div class="col-3">
                      <p class="h6">Admin</p>
                    </div>
                  </div>

                  <template v-for="(member, index) in localRole.memberOf" :key="member.index">
                    <div v-if="!member?.deleted" class="schema-editor__column d-flex row flex-nowrap form-group g-0">
                      <div class="col-8">
                        <SearchableDropdown
                          placeholder="type to search"
                          :options="existingRoleOptions"
                          :maxItem=20
                          v-model="member.name"
                        />
                      </div>
                      <div class="col-3 d-flex align-items-center">
                        <input type='checkbox' class="custom-checkbox" v-model="member.withAdmin"/>
                      </div>

                      <div :class="['col d-flex me-1', 'justify-content-end']">
                        <button @click='removeMember(localRole.memberOf, index)' type="button"
                          class="btn btn-icon btn-icon-danger ps-2 pe-2" title="Remove">
                          <i class="fas fa-circle-xmark"></i>
                        </button>
                      </div>
                    </div>
                  </template>

                  <div class="d-flex g-0 fw-bold mt-2">
                    <button @click='addMember(localRole.memberOf)' class="btn btn-outline-success btn-sm ms-auto">
                      Add Member
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer mt-auto justify-content-between">
            <button class="btn btn-outline-secondary"
              v-if="mode === operationModes.UPDATE"
              :disabled="!(v$.$invalid || hasChanges)"
              @click="revertChanges">
              Revert changes
            </button>
            <button type="button" class="btn btn-primary m-0 ms-auto"
              :disabled="v$.$invalid || !hasChanges"
              @click="saveRole">
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>

  <script>
  import SearchableDropdown from './SearchableDropdown.vue'
  import { required, between, maxLength, helpers } from '@vuelidate/validators'
  import { useVuelidate } from '@vuelidate/core'
  import isEmpty from 'lodash/isEmpty';
  import capitalize from 'lodash/capitalize';
  import { emitter } from '../emitter'
  import axios from 'axios'
  import moment from 'moment'
  import { operationModes } from '../constants';
  import { Modal } from 'bootstrap'
  import PreviewBox from './PreviewBox.vue';
  import { handleError } from '../logging/utils';

  export default {
    name: 'RoleModal',
    components: {
        SearchableDropdown,
        PreviewBox,
    },
    props: {
      mode: operationModes,
      treeNode: Object,
      workspaceId: String,
      databaseIndex: Number,
      version: String
    },
    data() {
      return {
        localRole: {},
        initialRole: {
          name: 'NewRole',
          // TODO: reimplement scram-sha-256 password string generation in JS, see pg_scram_sha256 for reference
          password: '',
          validUntil: null,
          connectionLimit: -1,
          canLogin: true,
          superuser: false,
          canCreateUsers: false,
          canCreateDatabases: false,
          inherit: false,
          canReplicate: false,
          canBypassRLS: false,
          members: [],
          memberOf: []
        },
        existingRoles: [],
        generatedSQL: null,
        modalInstance: null,
        hasChanges: false
      }
    },

    validations() {
      const validDate = function(value) {
        return !helpers.req(value) || moment(value).isValid() || value.toLowerCase() === 'infinity'
      }
      let baseRules = {
        localRole: {
          name: {
            required: required,
            maxLength: maxLength(63),
          },
          validUntil: {
            validDate: helpers.withMessage('Must be a parsable date/time, infinity, or empty string', validDate)
          },
          password: {
            maxLength: maxLength(1024),
          },

          connectionLimit: {
            between: between(-1,65535)
          }
        }
      }
      return baseRules;
    },

    setup() {
      return { v$: useVuelidate({ $lazy: false }) }
    },

    computed: {
      modalTitle() {
        if (this.mode === operationModes.UPDATE)
          return 'Edit Role'
        return 'Create Role'
      },
      existingRoleOptions() {
        return this.existingRoles.map((role) => role.name)
      }
    },

    watch: {
      // watch initialRole for changes for cases when it is changed by requesting role from the api
      initialRole: {
        handler(newVal, oldVal) {
          this.localRole = JSON.parse(JSON.stringify(newVal))
        },
        deep: true
      },
      // watch our local working copy for changes, generate new SQL when the change occurs
      localRole: {
        handler(newVal, oldVal) {
          this.v$.$validate()
          if(!this.v$.$invalid) {
            this.generateSQL()
          } else {
            let errs = this.v$.$errors.map((e) => `-- ${capitalize(e.$property)}: ${e.$message}`).join('\n')
            this.generatedSQL = `-- Invalid role definition --\n${errs}`
          }
        },
        deep: true
      }
    },
    created() {
      // allows for using operationModes in the template
      this.operationModes = operationModes
    },
    mounted() {
      if (this.mode === operationModes.UPDATE) {
        this.getRoleDetails()
      } else {
        this.localRole = JSON.parse(JSON.stringify(this.initialRole));
      }
      this.getExistingRoles()
      this.setupDatePicker()
      this.modalInstance = Modal.getOrCreateInstance('#roleModal')
      this.modalInstance.show()
    },
    methods: {
      getRoleDetails() {
        axios.post('/get_role_details/', {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
          oid: this.treeNode.data.oid
        })
        .then((resp) => {
          this.initialRole.name = resp.data.name
          this.initialRole.connectionLimit = resp.data.rolconnlimit
          this.initialRole.validUntil = resp.data.rolvaliduntil ? moment(resp.data.rolvaliduntil).format('YYYY-MM-DD HH:mm:ssZ') : null
          this.initialRole.canLogin = resp.data.rolcanlogin
          this.initialRole.canCreateDatabases = resp.data.rolcreatedb
          this.initialRole.canCreateUsers = resp.data.rolcreaterole
          this.initialRole.inherit = resp.data.rolinherit
          this.initialRole.superuser = resp.data.rolsuper
          this.initialRole.canReplicate = resp.data.rolreplication
          this.initialRole.canBypassRLS = resp.data.rolbypassrls
          this.initialRole.members = resp.data.members.map((m) => { return {name: m[0], withAdmin: m[1] == 'true'}})
          this.initialRole.memberOf = resp.data.member_of.map((m) => { return {name: m[0], withAdmin: m[1] == 'true'}})
        })
        .catch((error) => {
          handleError(error);
        })
      },
      getExistingRoles() {
        axios.post('/get_roles_postgresql/', {
          database_index: this.databaseIndex,
          workspace_id: this.workspaceId,
          oid: this.treeNode.data.oid
        })
        .then((resp) => {
          this.existingRoles = resp.data.data
        })
        .catch((error) => {
          handleError(error);
        })
      },
      addMember(collection) {
        const defaultRole = {name: this.existingRoles[0].name, withAdmin: false, new: true}
        collection.push(defaultRole)
      },
      removeMember(collection, index) {
        if(this.mode === operationModes.UPDATE && !collection[index].new) {
          collection[index].deleted = true;
        } else {
          collection.splice(index, 1)
        }
      },
      revertChanges() {
        this.localRole = JSON.parse(JSON.stringify(this.initialRole));
      },
      generateSQL() {
        let ret = ''
        const permVals = {
          'canLogin': ['NOLOGIN', 'LOGIN'],
          'superuser': ['NOSUPERUSER', 'SUPERUSER'],
          'canCreateUsers': ['NOCREATEROLE', 'CREATEROLE'],
          'canCreateDatabases': ['NOCREATEDB', 'CREATEDB'],
          'inherit': ['NOINHERIT', 'INHERIT'],
          'canReplicate': ['NOREPLICATION', 'REPLICATION'],
          'canBypassRLS': ['NOBYPASSRLS', 'BYPASSRLS']
        }
        let formatPermission = (permName) => {
          if(!Object.keys(permVals).includes(permName))
            return ''

          return permVals[permName][Number(this.localRole[permName])]
        }

        if (this.mode === operationModes.CREATE) {
          let permissions = Object.keys(permVals)
            .map(k => formatPermission(k))
            .filter(item => typeof item ==='string')
            .join(' ')

          let roleParts = [
            `CREATE ROLE "${this.localRole.name}"`,
            `${permissions}`
          ]

          if(this.localRole.password)
            roleParts.push(`PASSWORD '${this.localRole.password}'`)

          if(!isEmpty(this.localRole.validUntil))
            roleParts.push(`VALID UNTIL \'${moment(this.localRole.validUntil).toISOString() || 'infinity'}\'`)

          if(this.localRole.connectionLimit)
            roleParts.push(`CONNECTION LIMIT ${this.localRole.connectionLimit}`)

          let membershipParts = []
          this.localRole.members?.forEach((member) => {
            let withAdminPart = member.withAdmin ? ' WITH ADMIN OPTION' : '';
            membershipParts.push(`GRANT "${this.localRole.name}" to "${member.name}"${withAdminPart};`)
          })

          this.localRole.memberOf?.forEach((member) => {
            let withAdminPart = member.withAdmin ? ' WITH ADMIN OPTION' : '';
            membershipParts.push(`GRANT "${member.name}" to "${this.localRole.name}"${withAdminPart};`)
          })

          ret = `${roleParts.join('\n')};\n${membershipParts.join('\n')}`
          this.hasChanges = true
        } else if (this.mode === operationModes.UPDATE) {
          let roleParts = []
          let permissions = Object.keys(permVals)
            .filter(key => this.initialRole[key] != this.localRole[key])
            .map(k => formatPermission(k))
            .filter(item => typeof item ==='string')
            .join(' ')

          if(permissions)
            roleParts.push(permissions)

          if(this.initialRole.password != this.localRole.password)
            roleParts.push(`PASSWORD '${this.localRole.password}'`)

          if(this.initialRole.validUntil != this.localRole.validUntil)
            if(this.localRole.validUntil)
              roleParts.push(`VALID UNTIL \'${moment(this.localRole.validUntil).toISOString()}\'`)
            else
              roleParts.push(`VALID UNTIL 'infinity'`)

          if(this.initialRole.connectionLimit != this.localRole.connectionLimit)
            roleParts.push(`CONNECTION LIMIT ${this.localRole.connectionLimit}`)

          if(roleParts.length > 0)
            roleParts.unshift(`ALTER ROLE "${this.localRole.name}"`)

          if(this.initialRole.name != this.localRole.name)
            roleParts.unshift(`ALTER ROLE "${this.initialRole.name}" RENAME TO "${this.localRole.name}";`)

          let membershipParts = []
          this.localRole.members?.forEach((member, idx) => {
            let withAdminPart = member.withAdmin ? ' WITH ADMIN OPTION' : ''
            if(member.new) {
              membershipParts.push(`GRANT "${this.localRole.name}" to "${member.name}"${withAdminPart};`)
              return
            }
            if(member.deleted) {
              membershipParts.push(`REVOKE "${this.localRole.name}" FROM "${member.name}";`)
              return
            }
            let orig = this.initialRole.members[idx]
            if(orig.name !== member.name) {
              //selected role in membership was changed
              membershipParts.push(`REVOKE "${this.localRole.name}" FROM "${orig.name}";`);
              membershipParts.push(`GRANT "${this.localRole.name}" to "${member.name}"${withAdminPart};`)
            } else if (orig.withAdmin !== member.withAdmin) {
              // withAdmin flag changed
              if(member.withAdmin) {
                membershipParts.push(`GRANT "${this.localRole.name}" to "${member.name}"${withAdminPart};`)
              } else {
                membershipParts.push(`REVOKE ADMIN OPTION FOR "${this.localRole.name}" FROM "${member.name}";`);
              }
            }
          })

          this.localRole.memberOf?.forEach((member, idx) => {
            let withAdminPart = member.withAdmin ? ' WITH ADMIN OPTION' : ''
            if(member.new) {
              membershipParts.push(`GRANT "${member.name}" to "${this.localRole.name}"${withAdminPart};`)
              return
            }
            if(member.deleted) {
              membershipParts.push(`REVOKE "${member.name}" FROM "${this.localRole.name}";`)
              return
            }
            let orig = this.initialRole.memberOf[idx]
            if(orig.name !== member.name) {
              //selected role in membership was changed
              membershipParts.push(`REVOKE "${orig.name}" FROM "${this.localRole.name}";`);
              membershipParts.push(`GRANT "${member.name}" to "${this.localRole.name}"${withAdminPart};`)
            } else if (orig.withAdmin !== member.withAdmin) {
              // withAdmin flag changed
              if(member.withAdmin) {
                membershipParts.push(`GRANT "${member.name}" to "${this.localRole.name}"${withAdminPart};`)
              } else {
                membershipParts.push(`REVOKE ADMIN OPTION FOR "${member.name}" FROM "${this.localRole.name}";`);
              }
            }
          })

          if(roleParts.length > 0) {
            ret = `${roleParts.join('\n')}`
            ret += ret.endsWith(";") ? "\n" : ";\n"
          }

          if(membershipParts.length > 0)
            ret = `${ret}${membershipParts.join('\n')}`

          this.hasChanges = roleParts.length > 0 || membershipParts.length > 0
          if(!this.hasChanges)
            ret = '-- No changes --'
        }
        let roleDocLink = `-- https://www.postgresql.org/docs/${this.version}/user-manag.html`
        this.generatedSQL =`${roleDocLink}\n${ret}`
      },
      setupDatePicker(){
        $(this.$refs.datepicker).daterangepicker({
          autoUpdateInput: false,
          singleDatePicker: true,
          showDropdowns: true,
          previewUTC: true,
          timePicker: true,
          timePicker24Hour: true,
          locale: {
            format: moment.defaultFormat,
          },
          parentEl: this.$refs.daterangePicker,
        }, (start, end, label) => {
          this.localRole.validUntil = moment(start).format('YYYY-MM-DD HH:mm:ssZ')
        });
      },
      saveRole() {
        this.v$.$validate()
        if(!this.v$.$invalid) {
          axios.post('/execute_query/', {
            database_index: this.databaseIndex,
            workspace_id: this.workspaceId,
            query: this.generatedSQL
          })
          .then((resp) => {
            emitter.emit(`refreshTreeRecursive_${this.workspaceId}`, 'role_list');
            this.modalInstance.hide()
          })
          .catch((error) => {
            handleError(error);
          })
        }
      },
    },
  }
  </script>
