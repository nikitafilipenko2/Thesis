function filesPage() {
    return {
        dialogOpen: false,
        activeFileId: null,
        summaryType: 'extractive',
        modelName: 'cointegrated/rut5-base-absum',
        lengthParam: 3,
        loading: false,
        get submitUrl() {
            return this.activeFileId ? `/files/${this.activeFileId}/summarize/` : '';
        },
        openDialog(fileId) {
            this.activeFileId = fileId;
            this.summaryType = 'extractive';
            this.modelName = 'cointegrated/rut5-base-absum';
            this.lengthParam = 3;
            this.loading = false;
            const feedback = document.getElementById('file-summary-feedback');
            if (feedback) {
                feedback.innerHTML = '';
            }
            this.dialogOpen = true;
        },
        closeDialog() {
            this.dialogOpen = false;
            this.activeFileId = null;
            this.loading = false;
        }
    };
}
