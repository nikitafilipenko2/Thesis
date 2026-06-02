function summarizerApp() {
    return {
        // Состояние
        tab: 'text',
        text: '',
        model: 'extractive_textrank',
        sentenceCount: 5,
        minWords: 50,
        maxWords: 150,
        loading: false,
        result: '',
        processingTime: '',
        stats: '',
        fileInfo: '',
        fileInfoClass: 'alert-info',

        // Вычисляемые свойства
        get isExtractive() {
            return this.model.startsWith('extractive');
        },

        get resultHtml() {
            return this.result.replace(/\n/g, '<br>');
        },

        get totalSentences() {
            return countSentences(this.text);
        },

        get totalWords() {
            return countWords(this.text);
        },

        get maxSentencesAvailable() {
            return Math.min(20, Math.max(1, this.totalSentences));
        },

        get recommendedMin() {
            return Math.max(20, Math.floor(this.totalWords * 0.05));
        },

        get recommendedMax() {
            return Math.min(500, Math.floor(this.totalWords * 0.3));
        },

        // Анализ текста
        analyzeAndUpdateSliders() {
            const text = this.text.trim();
            if (!text) return;

            if (this.isExtractive) {
                let maxVal = this.maxSentencesAvailable;
                if (this.sentenceCount > maxVal) this.sentenceCount = maxVal;
                this.$nextTick(() => {
                    if (this.$refs.sentenceSlider) this.$refs.sentenceSlider.max = maxVal;
                });
            } else {
                let recMin = this.recommendedMin;
                let recMax = this.recommendedMax;
                if (this.minWords < recMin) this.minWords = recMin;
                if (this.maxWords > recMax) this.maxWords = recMax;
                if (this.minWords >= this.maxWords) {
                    this.minWords = recMin;
                    this.maxWords = recMax;
                }
                this.$nextTick(() => {
                    if (this.$refs.minWordsSlider) this.$refs.minWordsSlider.max = recMax - 10;
                    if (this.$refs.maxWordsSlider) {
                        this.$refs.maxWordsSlider.min = recMin + 10;
                        this.$refs.maxWordsSlider.max = recMax;
                    }
                });
            }
        },

        // Загрузка файла
        async uploadFile(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

            this.loading = true;
            this.fileInfo = '';

            try {
                const response = await fetch('/api/files/upload/', { method: 'POST', body: formData });
                const data = await response.json();

                if (response.ok) {
                    this.fileInfo = `✓ Файл загружен: ${data.original_filename}`;
                    this.fileInfoClass = 'alert-success';
                    this.tab = 'text';
                    this.text = data.extracted_text;
                    this.analyzeAndUpdateSliders();
                } else {
                    this.fileInfo = '✗ Ошибка: ' + (data.error || 'Неизвестная ошибка');
                    this.fileInfoClass = 'alert-danger';
                }
            } catch (error) {
                this.fileInfo = '✗ Ошибка при загрузке файла';
                this.fileInfoClass = 'alert-danger';
            } finally {
                this.loading = false;
                setTimeout(() => { this.fileInfo = ''; }, 3000);
            }
        },

        // Обновление модели
        updateModel() {
            localStorage.setItem('summarizer', JSON.stringify({
                text: this.text,
                model: this.model,
                sentenceCount: this.sentenceCount,
                minWords: this.minWords,
                maxWords: this.maxWords
            }));
            if (this.text.trim()) this.analyzeAndUpdateSliders();
        },

        // Суммаризация
        async summarize() {
            if (!this.text.trim()) {
                showAlert('Введите текст или загрузите файл', 'error');
                return;
            }

            this.loading = true;

            const lengthParam = this.isExtractive
                ? this.sentenceCount
                : { min: this.minWords, max: this.maxWords };

            try {
                const response = await fetch('/api/requests/summarize/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        input_text: this.text,
                        model: this.model,
                        length_param: lengthParam
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    this.result = data.output_text;
                    this.processingTime = `Время: ${data.processing_time.toFixed(2)} сек`;
                    const words = countWords(data.output_text);
                    const sentences = countSentences(data.output_text);
                    this.stats = `Слов: ${words}, предложений: ${sentences}`;
                    localStorage.setItem('summarizer', JSON.stringify({
                        text: this.text,
                        model: this.model,
                        sentenceCount: this.sentenceCount,
                        minWords: this.minWords,
                        maxWords: this.maxWords
                    }));
                    showAlert('Реферат готов!', 'success');
                } else {
                    showAlert('Ошибка: ' + (data.error || 'Неизвестная ошибка'), 'error');
                }
            } catch (error) {
                showAlert('Ошибка при отправке запроса', 'error');
            } finally {
                this.loading = false;
            }
        },

        copyResult() {
            copyToClipboard(this.result);
        },

        init() {
            const saved = localStorage.getItem('summarizer');
            if (saved) {
                const data = JSON.parse(saved);
                this.text = data.text || '';
                this.model = data.model || 'extractive_textrank';
                this.sentenceCount = data.sentenceCount || 5;
                this.minWords = data.minWords || 50;
                this.maxWords = data.maxWords || 150;
            }
            if (this.text.trim()) this.$nextTick(() => this.analyzeAndUpdateSliders());
            this.$watch('text', () => this.analyzeAndUpdateSliders());
            this.$watch('model', () => this.updateModel());
        }
    }
}