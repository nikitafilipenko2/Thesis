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
        },
        async submitForm() {
            if (!this.activeFileId || this.loading) {
                return;
            }

            const form = this.$refs.summaryForm;
            const feedback = document.getElementById('file-summary-feedback');
            const formData = new FormData(form);

            this.loading = true;
            if (feedback) {
                feedback.innerHTML = '';
            }

            try {
                const response = await fetch(this.submitUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'HX-Request': 'true',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin'
                });

                const redirectUrl = response.headers.get('HX-Redirect');
                if (redirectUrl) {
                    window.location.href = redirectUrl;
                    return;
                }

                const html = await response.text();
                if (feedback) {
                    feedback.innerHTML = html;
                }
            } catch {
                if (feedback) {
                    feedback.innerHTML = '<div class="alert alert-danger mb-0">Не удалось отправить запрос на суммаризацию.</div>';
                }
            } finally {
                this.loading = false;
            }
        }
    };
}
