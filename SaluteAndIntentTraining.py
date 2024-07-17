# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from sklearn.svm import SVC
# from sklearn.model_selection import train_test_split, GridSearchCV
# from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
# from sklearn.pipeline import Pipeline
# from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
# from joblib import dump
# import os

# # Ensure directory for saving models exists

# def load_data(file_path):
#     return pd.read_csv(file_path)

# def preprocess_data(df, text_column, label_column):
#     X_train, X_test, y_train, y_test = train_test_split(df[text_column], df[label_column], test_size=0.2, random_state=42)
#     vectorizer = CountVectorizer()
#     tfidf_transformer = TfidfTransformer()
    
#     X_train_counts = vectorizer.fit_transform(X_train)
#     X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    
#     X_test_counts = vectorizer.transform(X_test)
#     X_test_tfidf = tfidf_transformer.transform(X_test_counts)
    
#     # Save vectorizer and transformer for future use
#     dump(vectorizer, f'vectorizer_{text_column}.joblib')
#     dump(tfidf_transformer, f'tfidf_{text_column}.joblib')
    
#     return X_train_tfidf, X_test_tfidf, y_train, y_test

# def build_and_train_model(X_train, y_train, dataset_name):
#     param_grid = {
#         'C': [1, 10, 100],
#         'kernel': ['linear', 'rbf']
#     }
#     svc = SVC(probability=True)
#     clf = GridSearchCV(svc, param_grid, cv=5, scoring='accuracy', verbose=1)
#     clf.fit(X_train, y_train)
    
#     print(f"Best parameters for {dataset_name}: {clf.best_params_}")
#     dump(clf, f'{dataset_name}_SVC_model.joblib')
    
#     return clf

# def evaluate_model(clf, X_test, y_test, dataset_name):
#     y_pred = clf.predict(X_test)
#     acc = accuracy_score(y_test, y_pred)
#     print(f"Accuracy for {dataset_name}: {acc}")
#     print(classification_report(y_test, y_pred))
#     conf_mat = confusion_matrix(y_test, y_pred)
    
#     plt.figure(figsize=(8, 6))
#     plt.imshow(conf_mat, interpolation='nearest', cmap=plt.cm.Blues)
#     plt.title(f'Confusion Matrix - {dataset_name}')
#     plt.colorbar()
#     tick_marks = np.arange(len(set(y_test)))
#     plt.xticks(tick_marks, set(y_test), rotation=45)
#     plt.yticks(tick_marks, set(y_test))
#     plt.tight_layout()
#     plt.ylabel('True label')
#     plt.xlabel('Predicted label')
#     plt.savefig(f'{dataset_name}_confusion_matrix2.png')
#     plt.close()

# def main():
#     # Intent Classifier
#     intent_df = load_data('IntentLabelingDataset.csv')
#     X_train_intent, X_test_intent, y_train_intent, y_test_intent = preprocess_data(intent_df, 'Command', 'Label')
#     intent_clf = build_and_train_model(X_train_intent, y_train_intent, 'Intent')
#     evaluate_model(intent_clf, X_test_intent, y_test_intent, 'Intent')

#     # Salutation Classifier
#     salutation_df = load_data('SalutationDatabase.csv')
#     X_train_salutation, X_test_salutation, y_train_salutation, y_test_salutation = preprocess_data(salutation_df, 'Utterance', 'Label')
#     salutation_clf = build_and_train_model(X_train_salutation, y_train_salutation, 'Salutation')
#     evaluate_model(salutation_clf, X_test_salutation, y_test_salutation, 'Salutation')

# if __name__ == "__main__":
#     main()


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from joblib import dump
import os


def load_data(file_path):
    return pd.read_csv(file_path)

def preprocess_data(df, text_column, label_column, prefix):
    X_train, X_test, y_train, y_test = train_test_split(df[text_column], df[label_column], test_size=0.2, random_state=42)
    vectorizer = CountVectorizer()
    tfidf_transformer = TfidfTransformer()
    
    X_train_counts = vectorizer.fit_transform(X_train)
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    
    X_test_counts = vectorizer.transform(X_test)
    X_test_tfidf = tfidf_transformer.transform(X_test_counts)
    
    # Save vectorizer and transformer for future use with appropriate prefix
    dump(vectorizer, f'{prefix}_vectorizer_{text_column}.joblib')
    dump(tfidf_transformer, f'{prefix}_tfidf_{text_column}.joblib')
    
    return X_train_tfidf, X_test_tfidf, y_train, y_test

def build_and_train_model(X_train, y_train, prefix, dataset_name):
    param_grid = {
        'C': [1, 10, 100],
        'kernel': ['linear', 'rbf']
    }
    svc = SVC(probability=True)
    clf = GridSearchCV(svc, param_grid, cv=5, scoring='accuracy', verbose=1)
    clf.fit(X_train, y_train)
    
    print(f"Best parameters for {dataset_name}: {clf.best_params_}")
    # Save the model with appropriate prefix
    dump(clf, f'{prefix}_{dataset_name}_SVC_model.joblib')
    
    return clf

def evaluate_model(clf, X_test, y_test, prefix, dataset_name):
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy for {dataset_name}: {acc}")
    print(classification_report(y_test, y_pred))
    conf_mat = confusion_matrix(y_test, y_pred)
    
    plt.figure(figsize=(8, 6))
    plt.imshow(conf_mat, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title(f'Confusion Matrix - {dataset_name}')
    plt.colorbar()
    tick_marks = np.arange(len(set(y_test)))
    plt.xticks(tick_marks, set(y_test), rotation=45)
    plt.yticks(tick_marks, set(y_test))
    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.savefig(f'{prefix}_{dataset_name}_confusion_matrix.png')
    plt.close()

def main():
    # Intent Classifier
    intent_df = load_data('IntentLabelingDataset.csv')
    X_train_intent, X_test_intent, y_train_intent, y_test_intent = preprocess_data(intent_df, 'Command', 'Label', 'Intent')
    intent_clf = build_and_train_model(X_train_intent, y_train_intent, 'Intent', 'Intent')
    evaluate_model(intent_clf, X_test_intent, y_test_intent, 'Intent', 'Intent')

    # Salutation Classifier
    salutation_df = load_data('SalutationDatabase.csv')
    X_train_salutation, X_test_salutation, y_train_salutation, y_test_salutation = preprocess_data(salutation_df, 'Utterance', 'Label', 'Salutation')
    salutation_clf = build_and_train_model(X_train_salutation, y_train_salutation, 'Salutation', 'Salutation')
    evaluate_model(salutation_clf, X_test_salutation, y_test_salutation, 'Salutation', 'Salutation')

if __name__ == "__main__":
    main()
