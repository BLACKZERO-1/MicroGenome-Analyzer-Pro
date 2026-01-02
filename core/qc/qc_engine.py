import os
from PySide6.QtCore import QThread, Signal

class QCWorker(QThread):
    """
    Runs Quality Control analysis.
    Now calculates Per-Base Content (A, T, G, C distribution).
    """
    progress_signal = Signal(int)
    result_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, file_path, trim_threshold=20):
        super().__init__()
        self.file_path = file_path
        self.trim_threshold = trim_threshold

    def run(self):
        try:
            if not os.path.exists(self.file_path):
                self.error_signal.emit("File not found.")
                return

            # Data Structures
            stats = {
                "total_reads": 0,
                "total_bases": 0,
                "gc_content": 0,
                "avg_quality": 0,
                "quality_per_position": [],  # [30, 32, 28...]
                "base_content_per_pos": []   # [{'A':10, 'T':20...}, ...]
            }

            quality_sums = [] 
            base_counts_pos = [] # List of dicts per position
            
            read_count = 0
            total_quality_sum = 0
            
            with open(self.file_path, 'r') as f:
                while True:
                    header = f.readline()
                    if not header: break
                    seq = f.readline().strip()
                    plus = f.readline()
                    qual = f.readline().strip()
                    
                    read_count += 1
                    seq_len = len(seq)
                    stats["total_bases"] += seq_len

                    # Dynamic Expansion (if read is longer than expected)
                    if len(quality_sums) < seq_len:
                        diff = seq_len - len(quality_sums)
                        quality_sums.extend([0] * diff)
                        base_counts_pos.extend([{'A':0, 'C':0, 'G':0, 'T':0, 'N':0} for _ in range(diff)])

                    # Process Sequence & Quality
                    current_read_qual_sum = 0
                    
                    for i, (base, q_char) in enumerate(zip(seq, qual)):
                        # 1. Base Count
                        base = base.upper()
                        if base in base_counts_pos[i]:
                            base_counts_pos[i][base] += 1
                        
                        # 2. Quality Score
                        score = ord(q_char) - 33
                        quality_sums[i] += score
                        current_read_qual_sum += score
                    
                    total_quality_sum += (current_read_qual_sum / seq_len) if seq_len > 0 else 0

                    if read_count % 2000 == 0:
                        self.progress_signal.emit(read_count)

            if read_count == 0:
                self.error_signal.emit("File is empty.")
                return

            # --- Final Aggregation ---
            stats["total_reads"] = read_count
            
            # Avg Quality
            stats["avg_quality"] = round(total_quality_sum / read_count, 2)
            
            # Per Position Quality
            stats["quality_per_position"] = [round(x / read_count, 2) for x in quality_sums]

            # Per Position Base Content (%)
            total_gc_bases = 0
            
            # Convert counts to percentages for the graph
            processed_base_content = []
            for pos_counts in base_counts_pos:
                total_at_pos = sum(pos_counts.values())
                if total_at_pos == 0:
                    processed_base_content.append({'A':0, 'C':0, 'G':0, 'T':0})
                    continue
                
                # Calculate Global GC while we are here
                total_gc_bases += (pos_counts['G'] + pos_counts['C'])
                
                processed_base_content.append({
                    'A': (pos_counts['A'] / total_at_pos) * 100,
                    'C': (pos_counts['C'] / total_at_pos) * 100,
                    'G': (pos_counts['G'] / total_at_pos) * 100,
                    'T': (pos_counts['T'] / total_at_pos) * 100,
                })
            
            stats["base_content_per_pos"] = processed_base_content
            stats["gc_content"] = round((total_gc_bases / stats["total_bases"]) * 100, 2)

            self.result_signal.emit(stats)

        except Exception as e:
            self.error_signal.emit(str(e))

class TrimmingWorker(QThread):
    finished_signal = Signal(str)

    def __init__(self, file_path, quality_threshold=20):
        super().__init__()
        self.file_path = file_path
        self.threshold = quality_threshold

    def run(self):
        new_path = self.file_path.replace(".fastq", "_clean.fastq")
        if new_path == self.file_path: new_path += "_clean.fastq"

        with open(self.file_path, 'r') as old_f, open(new_path, 'w') as new_f:
            while True:
                header = old_f.readline()
                if not header: break
                seq = old_f.readline().strip()
                plus = old_f.readline()
                qual = old_f.readline().strip()

                cut_pos = len(qual)
                for i in range(len(qual) - 1, -1, -1):
                    if (ord(qual[i]) - 33) < self.threshold:
                        cut_pos = i
                    else:
                        break
                
                if cut_pos > 15: # Only keep if read is decent length
                    new_f.write(header + seq[:cut_pos] + "\n" + plus + qual[:cut_pos] + "\n")

        self.finished_signal.emit(new_path)