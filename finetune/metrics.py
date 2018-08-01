from sklearn.metrics import accuracy_score, recall_score, precision_score

from finetune.encoding import NLP


def _convert_to_token_list(annotations, doc_idx=None):
    tokens = []

    for annotation in annotations:
        start_idx = annotation.get('start')
        tokens.extend([
            {
                'start': start_idx + token.idx,
                'end': start_idx + token.idx + len(token.text),
                'text': token.text,
                'label': annotation.get('label'),
                'doc_idx': doc_idx
            }
            for token in NLP(annotation.get('text'))
        ])

    return tokens


def sequence_labeling_token_counts(true, predicted):
    """
    Return FP, FN, and TP counts
    """

    unique_classes = set([seq['label'] for seqs in true for seq in seqs])

    d = {
        cls_: {
            'false_positives': [],
            'false_negatives': [],
            'correct': []
        }
        for cls_ in unique_classes
    }
    
    for i, (true_list, pred_list) in enumerate(zip(true, predicted)):
        true_tokens = _convert_to_token_list(true_list, doc_idx=i)
        pred_tokens = _convert_to_token_list(pred_list, doc_idx=i)

        # correct + false negatives
        for true_token in true_tokens:
            for pred_token in pred_tokens:
                if (pred_token['start'] == true_token['start'] and 
                    pred_token['end'] == true_token['end']):

                    if pred_token['label'] == true_token['label']:
                        d[true_token['label']]['correct'].append(true_token)
                    else:
                        d[true_token['label']]['false_negatives'].append(true_token)
                        d[pred_token['label']]['false_positives'].append(pred_token)
                    
                    break
            else:
                d[true_token['label']]['false_negatives'].append(true_token)

        # false positives
        for pred_token in pred_tokens:
            for true_token in true_tokens:
                if (pred_token['start'] == true_token['start'] and 
                    pred_token['end'] == true_token['end']):
                    break
            else:
                d[pred_token['label']]['false_positives'].append(pred_token)
    
    return d


def seq_recall(true, predicted, count_fn):
    class_counts = count_fn(true, predicted)
    results = {}
    for cls_, counts in class_counts.items():
        FN = len(counts['false_negatives'])
        TP = len(counts['correct'])
        results[cls_] =  TP / float(FN + TP)
    return results


def seq_precision(true, predicted, count_fn):
    class_counts = count_fn(true, predicted)
    results = {}
    for cls_, counts in class_counts.items():
        FP = len(counts['false_positives'])
        TP = len(counts['correct'])
        results[cls_] = TP / float(FP + TP)
    return results
    

def sequence_labeling_token_precision(true, predicted):
    """
    Token level precision
    """
    return seq_precision(true, predicted, count_fn=sequence_labeling_token_counts)


def sequence_labeling_token_recall(true, predicted):
    """
    Token level recall
    """
    return seq_recall(true, predicted, count_fn=sequence_labeling_token_counts)


def sequences_overlap(true_seq, pred_seq):
    """
    Boolean return value indicates whether or not seqs overlap
    """
    start_contained = (pred_seq['start'] < true_seq['end'] and pred_seq['start'] >= true_seq['start'])
    end_contained = (pred_seq['end'] > true_seq['start'] and pred_seq['end'] <= true_seq['end'])
    return start_contained or end_contained


def sequence_labeling_overlaps(true, predicted):
    """
    Return FP, FN, and TP counts
    """
    unique_classes = set([annotation['label'] for annotations in true for annotation in annotations])

    d = {
        cls_: {
            'false_positives': [],
            'false_negatives': [],
            'correct': []
        }
        for cls_ in unique_classes
    }

    for i, (true_annotations, predicted_annotations) in enumerate(zip(true, predicted)):
        # add doc idx to make verification easier
        for annotations in [true_annotations, predicted_annotations]:
            for i, annotation in enumerate(annotations):
                annotation['doc_idx'] = i
        
        for true_annotation in true_annotations:
            for pred_annotation in predicted_annotations:
                if sequences_overlap(true_annotation, pred_annotation):
                    if pred_annotation['label'] == true_annotation['label']:
                        d[true_annotation['label']]['correct'].append(true_annotation)
                    else:
                        d[true_annotation['label']]['false_negatives'].append(true_annotation)
                        d[pred_annotation['label']]['false_positives'].append(pred_annotation)
                    break
            else:
                d[true_annotation['label']]['false_negatives'].append(true_annotation)

        for pred_annotation in predicted_annotations:
            for true_annotation in true_annotations:
                if (sequences_overlap(true_annotation, pred_annotation) and 
                    true_annotation['label'] == pred_annotation['label']):
                    break
            else:
                d[pred_annotation['label']]['false_positives'].append(pred_annotation)
        return d


def sequence_labeling_overlap_precision(true, predicted):
    """
    Sequence overlap precision
    """
    return seq_precision(true, predicted, count_fn=sequence_labeling_overlaps)


def sequence_labeling_overlap_recall(true, predicted):
    """
    Sequence overlap recall
    """
    return seq_recall(true, predicted, count_fn=sequence_labeling_overlaps)

