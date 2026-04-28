<template>
  <h2 class="fw-bold text-center mt-2 mb-3">Jobs</h2>
  <div class="card">
    <div class="card-body p-0">
      <ul class="list-group list-group-flush rounded-0">
        <li class="list-group-item d-flex row g-0 fw-bold">
          <div class="col-1">PID</div>
          <div class="col-2">Type</div>
          <div class="col-2">Server</div>
          <div class="col-2">Object</div>
          <div class="col-2">Start Time</div>
          <div class="col-1">Status</div>
          <div class="col-1">Duration</div>
          <div class="col-1">Actions</div>
        </li>

        <li v-for="job in jobList" :key="job.id" class="list-group-item d-flex row g-0">
          <div class="col-1">{{ job.utility_pid }}</div>
          <div class="col-2">{{ job.details.type }}</div>
          <div class="col-2">{{ job.details.server }}</div>
          <div class="col-2">{{ job.details.object }}</div>
          <div class="col-2">{{ job.start_time }}</div>
          <div class="col-1"> 
            <i :class="['fa-solid', {
              'fa-hourglass text-info' : jobStatus(job.process_state) === 'Running',
              'fa-ban text-warning' : jobStatus(job.process_state) === 'Terminated' || jobStatus(job.process_state) === 'Terminating',
              'fa-circle-check text-success' : jobStatus(job.process_state) === 'Finished',
              'fa-circle-exclamation text-danger' : jobStatus(job.process_state) === 'Failed'
            }]"
              data-bs-toggle="tooltip" data-placement="bottom" :title="jobStatus(job.process_state)"
            ></i>
          </div>
          <div class="col-1">{{ job.duration }}</div>
          <div class="col-1 d-flex justify-content-between align-items-start muted-text">
              <a class="btn btn-ghost btn-ghost-secondary" @click="getJobDetails(job.id)" title="View details">
                <i class="fa-solid fa-scroll fa-lg"></i>
              </a>
              <a :class="['btn btn-ghost btn-ghost-secondary', {'disabled': job.canStop }]" @click="stopJob(job.id)" title="Stop job">
                <i class="fa-solid fa-stop fa-lg"></i>
              </a>
              <a class="btn btn-ghost btn-ghost-secondary" @click="deleteJob(job.id)">
                <i class="fas fa-times fa-lg" title="Delete job"></i>
              </a>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { utilityJobStore } from "../stores/stores_initializer";
import axios from "axios";
import moment from "moment";
import { handleError } from "../logging/utils";

const JobState = {
  PROCESS_NOT_STARTED: 0,
  PROCESS_STARTED: 1,
  PROCESS_FINISHED: 2,
  PROCESS_TERMINATED: 3,
  /* Supported by front end only */
  PROCESS_TERMINATING: 10,
  PROCESS_FAILED: 11,
};

export default {
  data() {
    return {
      pendingJobId: [],
      jobList: [],
      workerId: "",
    };
  },
  mounted() {
    this.startWorker();
  },
  unmounted() {
    clearInterval(this.workerId);
  },
  emits: ['jobExit'],
  methods: {
    getJobList() {
      axios
        .get("/bgprocess/")
        .then((resp) => {
          this.jobList = resp.data.data.map((j) => {
            let processState = this.evaluateProcessState(j);
            return {
              ...j,
              start_time: moment(j.start_time).format(),
              process_state: processState,
              canStop: ![
                JobState.PROCESS_NOT_STARTED,
                JobState.PROCESS_STARTED,
              ].includes(processState),
            };
          });
          this.checkPending();
        })
        .catch((error) => {
          handleError(error);
        });
    },
    startWorker() {
      this.getJobList();
      this.pendingJobId = this.jobList
        .filter((p) => p.process_state === JobState.PROCESS_STARTED)
        .map((p) => p.id);
      this.workerId = setInterval(() => {
        if (this.pendingJobId.length > 0) {
          this.getJobList();
        }
      }, 1000);
    },
    startJob(job_id, desc) {
      this.pendingJobId.push(job_id);
    },
    stopJob(job_id) {
      this.jobList.find((p) => p.id == job_id).process_state =
        JobState.PROCESS_TERMINATING;
      axios
        .post(`/bgprocess/stop/${job_id}/`)
        .then((resp) => {
          this.jobList.find((p) => p.id == job_id).process_state =
            JobState.PROCESS_TERMINATED;
        })
        .catch((error) => {
          handleError(error);
        });
    },
    deleteJob(job_id) {
      axios
        .post(`/bgprocess/delete/${job_id}/`)
        .then((resp) => {
          this.$emit('jobExit', job_id)
          this.pendingJobId = this.pendingJobId.filter((id) => id != job_id);
          this.getJobList();
        })
        .catch((error) => {
          handleError(error);
        });
    },
    jobStatus(process_state) {
      if (process_state === JobState.PROCESS_STARTED) {
        return "Running";
      } else if (process_state === JobState.PROCESS_FINISHED) {
        return "Finished";
      } else if (process_state === JobState.PROCESS_TERMINATED) {
        return "Terminated";
      } else if (process_state === JobState.PROCESS_TERMINATING) {
        return "Terminating";
      } else if (process_state === JobState.PROCESS_FAILED) {
        return "Failed";
      }
      return "";
    },
    evaluateProcessState(p) {
      let retState = p.process_state;
      if (
        (p.end_time || p.exit_code != null) &&
        p.process_state == JobState.PROCESS_STARTED
      ) {
        retState = JobState.PROCESS_FINISHED;
      }
      if (retState == JobState.PROCESS_FINISHED && p.exit_code != 0) {
        retState = JobState.PROCESS_FAILED;
      }
      return retState;
    },
    checkPending() {
      const completedJobIds = this.jobList
        .filter((j) => {
          if (
            ![
              JobState.PROCESS_NOT_STARTED,
              JobState.PROCESS_STARTED,
              JobState.PROCESS_TERMINATING,
            ].includes(j.process_state)
          ) {
            return true;
          }
        })
        .map((j) => j.id);
      this.pendingJobId = this.pendingJobId.filter((id) => {
        if (completedJobIds.includes(id)) {
          let j = this.jobList.find((j) => j.id == id);
          this.$emit('jobExit', id)
          if (j.process_state != JobState.PROCESS_TERMINATED)
            this.sendNotifyJobFinished(j.description, j.process_state, () =>
              this.getJobDetails(j.id, event)
            );
          return false;
        }
        return true;
      });
    },
    createNotifyMessage(title, desc) {
      return `<div class="v-toast__body p-0">
                  <h3 class="fw-bold">${title}</h3>
                  <p>${desc}</p>
                  <div class="text-end">
                    <button class="btn v-toast__details fw-bold">View details</button>
                  </div>
              </div>`;
    },
    sendNotifyJobFinished(desc, process_state, onClickProcess) {
      let success = true;
      let message = this.createNotifyMessage("Job finished", desc);
      if (process_state == JobState.PROCESS_FAILED) {
        message = this.createNotifyMessage("Job terminated", desc);
        success = false;
      }
      if (success) {
        this.$toast.success(message, {
          onClick: onClickProcess,
        });
      } else {
        this.$toast.error(message, {
          onClick: onClickProcess,
        });
      }
    },
    getJobDetails(job_id, event) {
      if (!event || event.target.tagName === "BUTTON") {
        const job = JSON.parse(
          JSON.stringify(this.jobList.find((j) => j.id == job_id))
        );
        utilityJobStore.setJob(job);
      } else {
        event.stopPropagation();
      }
    },
  },
};
</script>
