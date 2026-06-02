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
        get sentenceSliderMax() {
            return Math.min(20, Math.max(1, this.totalSentences || 1));
        },
        get abstractiveMinBound() {
            return 20;
        },
        get abstractiveMaxBound() {
            return Math.max(30, Math.min(500, Math.floor(this.totalWords * 0.3) || 150));
        },
        get minWordsSliderMax() {
            return Math.max(this.abstractiveMinBound, this.abstractiveMaxBound - 10);
        },
        get maxWordsSliderMin() {
            return Math.min(this.abstractiveMaxBound, this.minWords + 10);
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
        normalizeExtractiveRange() {
            if (this.sentenceCount > this.sentenceSliderMax) {
                this.sentenceCount = this.sentenceSliderMax;
            }
            if (this.sentenceCount < 1) {
                this.sentenceCount = 1;
            }
        },
        normalizeAbstractiveRange() {
            const sliderMax = this.abstractiveMaxBound;
            const minSliderMax = this.minWordsSliderMax;

            if (this.minWords < this.abstractiveMinBound) {
                this.minWords = this.abstractiveMinBound;
            }
            if (this.minWords > minSliderMax) {
                this.minWords = minSliderMax;
            }

            if (this.maxWords < this.minWords + 10) {
                this.maxWords = this.minWords + 10;
            }
            if (this.maxWords > sliderMax) {
                this.maxWords = sliderMax;
            }

            if (this.maxWords <= this.minWords) {
                this.maxWords = Math.min(sliderMax, this.minWords + 10);
            }
            if (this.minWords >= this.maxWords) {
                this.minWords = Math.max(this.abstractiveMinBound, this.maxWords - 10);
            }
        },
        analyzeAndUpdateSliders() {
            if (!this.text.trim()) {
                return;
            }

            if (this.isExtractive) {
                this.normalizeExtractiveRange();
                return;
            }

            this.normalizeAbstractiveRange();
        },
        updateModel() {
            this.analyzeAndUpdateSliders();
            localStorage.setItem('summarizer', JSON.stringify({
                text: this.text,
                model: this.model,
                sentenceCount: this.sentenceCount,
                minWords: this.minWords,
                maxWords: this.maxWords
            }));
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

            this.analyzeAndUpdateSliders();

            this.$watch('text', () => {
                this.analyzeAndUpdateSliders();
                this.updateModel();
            });
            this.$watch('model', () => this.updateModel());
            this.$watch('sentenceCount', () => this.updateModel());
            this.$watch('minWords', () => {
                this.normalizeAbstractiveRange();
                this.updateModel();
            });
            this.$watch('maxWords', () => {
                this.normalizeAbstractiveRange();
                this.updateModel();
            });

            document.body.addEventListener('homeFileUploaded', event => {
                this.text = event.detail.text || '';
                this.tab = 'text';
                this.updateModel();
                showAlert(`Файл загружен: ${event.detail.filename}`, 'success');
            });
        }
    };
}
