function summarizerApp() {
    return {
        tab: 'text',
        text: '',
        model: 'extractive_textrank',
        sentenceCount: 5,
        minWords: 50,
        maxWords: 150,
        loading: false,
        get isExtractive() {
            return this.model.startsWith('extractive');
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
            return Math.min(500, Math.max(30, Math.floor(this.totalWords * 0.3)));
        },
        normalizeSavedModel(model) {
            const allowedModels = [
                'extractive_textrank',
                'extractive_lsa',
                'extractive_lexrank',
                'cointegrated/rut5-base-absum',
                'IlyaGusev/rut5_base_sum_gazeta',
                'Azerotorez/Scientific_paper_rusumm',
                'IlyaGusev/mbart_ru_sum_gazeta'
            ];
            return allowedModels.includes(model) ? model : 'extractive_textrank';
        },
        analyzeAndUpdateSliders() {
            const text = this.text.trim();
            if (!text) {
                return;
            }

            if (this.isExtractive) {
                const maxVal = this.maxSentencesAvailable;
                if (this.sentenceCount > maxVal) {
                    this.sentenceCount = maxVal;
                }
                this.$nextTick(() => {
                    if (this.$refs.sentenceSlider) {
                        this.$refs.sentenceSlider.max = maxVal;
                    }
                });
                return;
            }

            const recMin = this.recommendedMin;
            const recMax = this.recommendedMax;
            if (this.minWords < recMin) {
                this.minWords = recMin;
            }
            if (this.maxWords > recMax) {
                this.maxWords = recMax;
            }
            if (this.minWords >= this.maxWords) {
                this.minWords = recMin;
                this.maxWords = Math.max(recMin + 10, recMax);
            }
            this.$nextTick(() => {
                if (this.$refs.minWordsSlider) {
                    this.$refs.minWordsSlider.max = Math.max(recMin, recMax - 10);
                }
                if (this.$refs.maxWordsSlider) {
                    this.$refs.maxWordsSlider.min = recMin + 10;
                    this.$refs.maxWordsSlider.max = recMax;
                }
            });
        },
        updateModel() {
            localStorage.setItem('summarizer', JSON.stringify({
                text: this.text,
                model: this.model,
                sentenceCount: this.sentenceCount,
                minWords: this.minWords,
                maxWords: this.maxWords
            }));
            if (this.text.trim()) {
                this.analyzeAndUpdateSliders();
            }
        },
        init() {
            const saved = localStorage.getItem('summarizer');
            if (saved) {
                const data = JSON.parse(saved);
                this.text = data.text || '';
                this.model = this.normalizeSavedModel(data.model);
                this.sentenceCount = data.sentenceCount || 5;
                this.minWords = data.minWords || 50;
                this.maxWords = data.maxWords || 150;
            }
            if (this.text.trim()) {
                this.$nextTick(() => this.analyzeAndUpdateSliders());
            }
            this.$watch('text', () => this.analyzeAndUpdateSliders());
            this.$watch('model', () => this.updateModel());
            document.body.addEventListener('homeFileUploaded', event => {
                this.text = event.detail.text || '';
                this.tab = 'text';
                this.updateModel();
                showAlert(`Файл загружен: ${event.detail.filename}`, 'success');
            });
        }
    };
}
