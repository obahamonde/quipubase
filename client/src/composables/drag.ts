export const useDrag = <T extends { name?: string; id?: string }>() => {
  const isOverDropzone = ref(false);
  const dropzone = ref<T[]>([]);
  const draggableData = ref<T>();
  const onDragStart = (e: DragEvent, func: T) => {
    e.dataTransfer?.setData("application/json", JSON.stringify(func));
  };
  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    isOverDropzone.value = true;
  };
  const onDragLeave = (e: DragEvent) => {
    e.preventDefault();
    isOverDropzone.value = false;
  };
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    isOverDropzone.value = false;
    ("");

    const data = e.dataTransfer?.getData("application/json");
    if (data) {
      const func = JSON.parse(data);
      if (!dropzone.value.find((d) => d.name === func.name)) {
        dropzone.value.push(func);
      }
    }
  };

  const el = ref<HTMLElement>();

  onMounted(() => {
    if (el.value) {
      el.value.addEventListener("dragover", onDragOver);
      el.value.addEventListener("dragleave", onDragLeave);
      el.value.addEventListener("drop", onDrop);
    }
  });
  onUnmounted(() => {
    if (el.value) {
      el.value.removeEventListener("dragover", onDragOver);
      el.value.removeEventListener("dragleave", onDragLeave);
      el.value.removeEventListener("drop", onDrop);
    }
  });

  watch(draggableData, (newVal, oldVal) => {
    if (newVal !== oldVal) {
      console.log(newVal);
    }
  });

  return {
    dropzone,
    draggableData,
    onDragStart,
    isOverDropzone,
    el,
  };
};
