<!--
  -*- coding: utf-8 -*-

  -------------------------------------------------------------------------
  COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
  Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
  Commercial use requires prior written consent from all copyright holders.
  See LICENSE for full terms. Thank you for keeping the rules.
  https://github.com/monjyu1101
  -------------------------------------------------------------------------
-->

<script setup lang="ts">
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch } from 'vue';

interface 工程型 {
  工程ID: string
  工程名: string
  工程備考?: string
}

interface 生産型 {
  生産伝票ID: string
  生産開始日時: string
  生産終了日時: string
  工程ID: string
  生産区分ID: string
  生産内容?: string
  生産備考?: string
  [key: string]: any
}

const props = defineProps({
  工程リスト: {
    type: Array as () => 工程型[],
    default: () => []
  },
  生産リスト: {
    type: Array as () => 生産型[],
    default: () => []
  },
  対象日付: {
    type: Date,
    required: true
  }
});

const emit = defineEmits([
  'update-schedule-resize',
  'update-schedule-drop',
  'open-edit-form'
]);

let draggingScheduleId: string | null = null;
let resizeState: any = null;

const displayHours = computed(() => Array.from({ length: 10 }, (_, index) => 8 + index));

const formatDate = (date: Date): string => {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${month}/${day}`;
};

const formatTime = (date: Date): string => {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
};

const getCellWidth = () => {
  const cell = document.querySelector('.droppable-area');
  if (cell) {
    const width = cell.getBoundingClientRect().width;
    if (width > 0) return width;
  }

  const grid = document.querySelector('.daily-grid-seisan');
  if (!grid) return 0;

  const gridWidth = grid.getBoundingClientRect().width;
  const processColumnWidth = 150;
  const timeColumns = 10;
  const gap = 1;

  const totalGaps = 11;
  const availableWidth = gridWidth - processColumnWidth - (totalGaps * gap);
  const cellWidth = availableWidth / timeColumns;
  return cellWidth;
};

const clearScheduleElements = () => {
  document.querySelectorAll('.schedule-item-seisan-day').forEach((item) => item.remove());
};

const renderSchedules = () => {
  clearScheduleElements();
  if (!props.対象日付) return;

  const displayStartDate = new Date(props.対象日付);
  displayStartDate.setHours(0, 0, 0, 0);
  const displayEndDate = new Date(displayStartDate);
  displayEndDate.setHours(23, 59, 59, 999);

  const rangeStartHour = 8;
  const rangeEndHour = 18;

  props.生産リスト.forEach((schedule) => {
    const startDateTime = new Date(schedule.生産開始日時);
    const endDateTime = new Date(schedule.生産終了日時);

    if (endDateTime < displayStartDate || startDateTime > displayEndDate) return;

    renderSchedule(schedule, startDateTime, endDateTime, props.対象日付, rangeStartHour, rangeEndHour);
  });
};

const renderSchedule = (schedule, startTime, endTime, currentDay, rangeStartHour, rangeEndHour) => {
  const scheduleStartDate = new Date(startTime); scheduleStartDate.setHours(0,0,0,0);
  const scheduleEndDate = new Date(endTime); scheduleEndDate.setHours(0,0,0,0);
  const currentDayStart = new Date(currentDay); currentDayStart.setHours(0,0,0,0);

  let displayStartHour;
  let displayEndHour;
  let isPartialStart = false;
  let isPartialEnd = false;

  if (startTime.getTime() < currentDayStart.getTime() + rangeStartHour * 3600000) {
    displayStartHour = rangeStartHour;
    isPartialStart = true;
  } else {
    displayStartHour = startTime.getHours();
  }

  const rangeEndTimestamp = currentDayStart.getTime() + rangeEndHour * 3600000;
  if (endTime.getTime() > rangeEndTimestamp) {
    displayEndHour = rangeEndHour;
    isPartialEnd = true;
  } else {
    let endHour = endTime.getHours();
    const endMinutes = endTime.getMinutes();
    if (endMinutes > 0) endHour++;
    displayEndHour = endHour;
  }

  if (scheduleStartDate < currentDayStart) isPartialStart = true;
  if (scheduleEndDate > currentDayStart) isPartialEnd = true;

  if (displayStartHour >= rangeEndHour || displayEndHour <= rangeStartHour) return;

  const startCellId = `seisan-day-cell-${schedule.工程ID}-${String(displayStartHour).padStart(2, '0')}:00`;
  const targetCell = document.getElementById(startCellId);
  if (!targetCell) return;

  const visibleDuration = displayEndHour - displayStartHour;
  if (visibleDuration <= 0) return;

  let startTimeStr = `${formatDate(startTime)} ${formatTime(startTime)}`;
  let endTimeStr = `～${formatDate(endTime)} ${formatTime(endTime)}`;
  if (isPartialStart) {
    startTimeStr = `\u25c0${formatDate(startTime)} ${formatTime(startTime)}`;
  }
  if (isPartialEnd) {
    endTimeStr = `～${formatDate(endTime)} ${formatTime(endTime)}\u25b6`;
  }

  const categoryName = schedule.生産区分名 || '';
  const content = schedule.生産内容 || '';
  const backgroundColor = schedule.配色背景 || '#007bff';
  const borderColor = schedule.配色枠 || '#0056b3';
  const textColor = schedule.配色前景 || '#ffffff';

  const cellWidth = getCellWidth();
  if (cellWidth === 0) return;

  const gapWidth = 1;
  const totalWidth = (cellWidth * visibleDuration) + (gapWidth * (visibleDuration - 1));

  const grid = document.getElementById('daily-grid-seisan');
  if (!grid) return;

  const gridRect = grid.getBoundingClientRect();
  const cellRect = targetCell.getBoundingClientRect();

  const left = cellRect.left - gridRect.left;
  const top = cellRect.top - gridRect.top;

  const scheduleElement = document.createElement('div');
  scheduleElement.className = 'schedule-item-seisan-day';
  scheduleElement.title = schedule.生産内容 || '';
  scheduleElement.style.position = 'absolute';
  scheduleElement.style.left = `${left}px`;
  scheduleElement.style.top = `${top}px`;
  scheduleElement.style.width = `${totalWidth}px`;
  scheduleElement.style.maxWidth = `${totalWidth}px`;
  scheduleElement.style.backgroundColor = backgroundColor;
  scheduleElement.style.border = `1px solid ${borderColor}`;
  scheduleElement.style.borderLeft = `6px solid ${borderColor}`;
  scheduleElement.style.color = textColor;
  scheduleElement.innerHTML = `
    <div class="schedule-text schedule-text-start">${startTimeStr} ${categoryName}</div>
    <div class="schedule-text schedule-text-center">${content || '&nbsp;'}</div>
    <div class="schedule-text schedule-text-end">${endTimeStr}</div>
  `;

  scheduleElement.addEventListener('dblclick', (event) => {
    event.preventDefault();
    event.stopPropagation();
    emit('open-edit-form', schedule.生産伝票ID);
  });
  scheduleElement.addEventListener('click', (event) => {
    event.stopPropagation();
  });
  scheduleElement.addEventListener('dragstart', (event) => {
    draggingScheduleId = schedule.生産伝票ID;
    event.dataTransfer?.setData('text/plain', schedule.生産伝票ID);
  });
  scheduleElement.addEventListener('dragend', () => {
    draggingScheduleId = null;
  });
  scheduleElement.draggable = true;

  if (!isPartialStart) {
    const leftHandle = document.createElement('div');
    leftHandle.className = 'resize-handle resize-handle-left';
    leftHandle.addEventListener('pointerdown', (event) => {
      startResize(event, schedule, 'left', scheduleElement);
    });
    leftHandle.addEventListener('click', e => e.stopPropagation());
    leftHandle.addEventListener('dblclick', e => e.stopPropagation());
    scheduleElement.appendChild(leftHandle);
  }

  if (!isPartialEnd) {
    const rightHandle = document.createElement('div');
    rightHandle.className = 'resize-handle resize-handle-right';
    rightHandle.addEventListener('pointerdown', (event) => {
      startResize(event, schedule, 'right', scheduleElement);
    });
    rightHandle.addEventListener('click', e => e.stopPropagation());
    rightHandle.addEventListener('dblclick', e => e.stopPropagation());
    scheduleElement.appendChild(rightHandle);
  }

  grid.style.position = 'relative';
  grid.appendChild(scheduleElement);
};

const startResize = (event, schedule, direction, element) => {
  event.preventDefault();
  event.stopPropagation();

  const cellWidth = getCellWidth();
  if (!cellWidth) return;

  const rect = element.getBoundingClientRect();
  const originalLeft = parseFloat(element.style.left) || 0;

  element.draggable = false;

  resizeState = {
    schedule,
    direction,
    startX: event.clientX,
    originalWidth: rect.width,
    originalLeft: originalLeft,
    element,
    cellWidth
  };

  const onMove = (moveEvent) => {
    if (!resizeState) return;
    moveEvent.preventDefault();
    const delta = moveEvent.clientX - resizeState.startX;

    const gapWidth = 1;
    const cellWithGap = resizeState.cellWidth + gapWidth;
    const deltaHours = Math.round(delta / cellWithGap);
    const snappedDelta = deltaHours * cellWithGap;

    if (resizeState.direction === 'left') {
      const newLeft = resizeState.originalLeft + snappedDelta;
      const newWidth = resizeState.originalWidth - snappedDelta;
      if (newWidth > cellWithGap - 10) {
        resizeState.element.style.left = `${newLeft}px`;
        resizeState.element.style.width = `${newWidth}px`;
      }
    } else {
      const newWidth = resizeState.originalWidth + snappedDelta;
      if (newWidth > cellWithGap - 10) {
        resizeState.element.style.width = `${newWidth}px`;
      }
    }
  };

  const onUp = (upEvent) => {
    const state = resizeState;
    resizeState = null;
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);

    if (element) {
      element.draggable = true;
    }

    if (!state) return;

    const delta = upEvent.clientX - state.startX;
    const gapWidth = 1;
    const cellWithGap = state.cellWidth + gapWidth;
    const deltaHours = Math.round(delta / cellWithGap);

    if (deltaHours !== 0) {
      emit('update-schedule-resize', { schedule: state.schedule, direction: state.direction, deltaHours });
    } else {
      renderSchedules();
    }
  };

  window.addEventListener('pointermove', onMove);
  window.addEventListener('pointerup', onUp);
};

const handleDrop = (event, processId, timeSlot) => {
  event.preventDefault();
  const scheduleId = event.dataTransfer?.getData('text/plain') || draggingScheduleId;
  if (!scheduleId) return;
  emit('update-schedule-drop', { scheduleId, processId, timeSlot });
};

const openProductionScheduleForm = (processId, timeSlot) => {
  emit('open-edit-form', null, processId, timeSlot);
};

watch(() => props.生産リスト, () => {
  nextTick(renderSchedules);
}, { deep: true });

watch(() => props.対象日付, () => {
  nextTick(renderSchedules);
});

onMounted(() => {
  setTimeout(renderSchedules, 100);
  window.addEventListener('resize', renderSchedules);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderSchedules);
  clearScheduleElements();
});
</script>

<template>
  <div class="daily-grid-seisan" id="daily-grid-seisan">
    <div class="grid-cell header-cell">工程</div>
    <div
      v-for="hour in displayHours"
      :key="hour"
      class="grid-cell header-cell"
    >
      <div class="time-header">{{ String(hour).padStart(2, '0') }}:00</div>
    </div>

    <template v-for="process in 工程リスト" :key="process.工程ID">
      <div class="grid-cell vehicle-cell">
        <div class="vehicle-id">{{ process.工程ID }} {{ process.工程備考 || '' }}</div>
        <div class="vehicle-name">{{ process.工程名 }}</div>
      </div>
      <div
        v-for="hour in displayHours"
        :key="`${process.工程ID}-${hour}`"
        :id="`seisan-day-cell-${process.工程ID}-${String(hour).padStart(2, '0')}:00`"
        class="grid-cell droppable-area empty-cell"
        @dragover.prevent
        @drop="(event) => handleDrop(event, process.工程ID, `${String(hour).padStart(2, '0')}:00`)"
        @dblclick="openProductionScheduleForm(process.工程ID, `${String(hour).padStart(2, '0')}:00`)"
      ></div>
    </template>
  </div>
</template>

<style scoped>
.daily-grid-seisan {
  display: grid;
  grid-template-columns: 150px repeat(10, 1fr);
  grid-gap: 1px;
  background-color: #ccc;
  border: 1px solid #ccc;
  height: auto;
  width: calc(100% - 25px);
  margin: 0 10px 10px 15px;
  position: relative;
  user-select: none;
}

.grid-cell {
  background-color: #fff;
  padding: 0;
  height: 70px;
  min-height: 70px;
  position: relative;
  border: 1px solid #ddd;
  box-sizing: border-box;
}

.header-cell {
  background-color: #2c3e50;
  color: #fff;
  font-weight: bold;
  text-align: center;
  font-size: 16px;
  border-bottom: 2px solid #007bff;
  line-height: 1;
  height: 32px;
  min-height: 32px;
  max-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: none;
  border-left: none;
  border-right: none;
}

.vehicle-cell {
  background-color: #e6e6e6;
  font-weight: bold;
  padding: 8px 5px;
  font-size: 12px;
  border-right: 2px solid #007bff;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.vehicle-id {
  font-size: 12px;
  text-align: left;
}

.vehicle-name {
  font-size: 14px;
  text-align: center;
  margin-top: 2px;
}

.time-header {
  text-align: center;
  font-size: 13px;
  line-height: 1;
  height: 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.empty-cell {
  cursor: pointer;
}

.empty-cell:hover {
  background-color: #f8f9fa;
}
</style>

<style>
/* scoped外 */
.schedule-item-seisan-day {
  background-color: #007bff;
  color: #fff;
  border: 1px solid #0056b3;
  border-left: 8px solid #0056b3;
  border-radius: 3px;
  padding: 3px 6px;
  margin: 0;
  font-size: 14px;
  cursor: pointer;
  position: absolute;
  top: 0;
  left: 0;
  height: 65px;
  min-height: 65px;
  overflow: hidden;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  z-index: 5;
}

.schedule-item-seisan-day:hover {
  z-index: 10;
}

.schedule-text {
  width: 100%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.schedule-text-start {
  text-align: left;
  padding-left: 4px;
  font-size: 12px;
}

.schedule-text-center {
  text-align: center;
  font-size: 14px;
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.schedule-text-end {
  text-align: right;
  padding-right: 4px;
  font-size: 12px;
}

.resize-handle {
  position: absolute;
  top: 0;
  width: 20px;
  height: 100%;
  cursor: ew-resize;
  z-index: 30;
  user-select: none;
  -webkit-user-select: none;
  pointer-events: auto;
}

.resize-handle-left {
  left: 0;
}

.resize-handle-right {
  right: 0;
}
</style>
