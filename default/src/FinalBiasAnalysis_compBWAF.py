import numpy as np
from sklearn import metrics
from sklearn.metrics import accuracy_score

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    cptDI
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def cptDI(S, Y):
    """
    S is the sensitive variable. S=0 if minority / S=1 if majority
    Y is the outcome variable. Y=0 if favorable (no default) / Y=1 if adverse (default)
    """
    n = 1.0 * Y.shape[0]

    pi_1 = np.mean(S)  # P(S=1)
    pi_0 = 1 - pi_1  # P(S=0)
    p_1 = np.mean(S * (1 - Y))  # P(Y=0|S=1) [Favorable outcome for privileged]
    p_0 = np.mean((1 - S) * (1 - Y))  # P(Y=0|S=0) [Favorable outcome for unprivileged]

    DI = (p_0 / pi_0) / (p_1 / pi_1)  # Disparate Impact ratio
    return DI


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Make_Kfold_boxplots
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold

# from sklearn.linear_model import LogisticRegression
# from sklearn.tree import DecisionTreeClassifier
# from sklearn.ensemble import RandomForestClassifier
# import lightgbm as lgb


def Make_Kfold_boxplots(
    list_classifiers,
    list_classifierNames,
    S,
    X,
    y,
    nsplits,
    printAverageRes=False,
    printAverageConfusionMatrices=False,
    Show_DI_boxPlotsOnly=False,
    PrefixFigNames="cur",
):
    """
    Generate boxplots of the discriminate impacts and the accuracies
    obtained on different classifier on the data [X,y]. The label of
    the sensitive variable for each observation is in S.
    """

    # 1) create the lists in which the DI and the accuracies will be stored
    lst_DI_Ref = []
    lst_DI_clfs = []
    for i in range(len(list_classifiers)):
        lst_DI_clfs.append([])

    lst_Acc_clfs = []
    for i in range(len(list_classifiers)):
        lst_Acc_clfs.append([])

    lst_tnr = []
    lst_tnr_S0 = []
    lst_tnr_S1 = []
    for i in range(len(list_classifiers)):
        lst_tnr.append([])
        lst_tnr_S0.append([])
        lst_tnr_S1.append([])

    lst_tpr = []
    lst_tpr_S0 = []
    lst_tpr_S1 = []
    for i in range(len(list_classifiers)):
        lst_tpr.append([])
        lst_tpr_S0.append([])
        lst_tpr_S1.append([])

    if printAverageConfusionMatrices == True:
        lst_CM = []
        for i in range(len(list_classifiers)):
            lst_CM.append(np.zeros((2, 2)))

    # 2) Use 10-fold cross-validation to measure the strategies accuracy and D.I.
    kf = KFold(n_splits=nsplits, shuffle=True)
    for train, test in kf.split(X):
        # split the train and test data
        X_train = X[train]
        y_train = y[train]
        X_test = X[test]
        y_test = y[test]
        S_test = S[test]

        # add the D.I. of the true tested data
        DI_Ref = cptDI(S_test.ravel(), y_test.ravel())
        lst_DI_Ref.append(DI_Ref)

        # train the three classifiers and predict y on the test data
        for i in range(len(list_classifiers)):
            list_classifiers[i].fit(X_train, y_train.ravel())
            y_test_pred = list_classifiers[i].predict(X_test)

            DI_clf = cptDI(S_test.ravel(), y_test_pred.ravel())
            lst_DI_clfs[i].append(DI_clf)

            acc_clf = accuracy_score(y_test.ravel(), y_test_pred.ravel())
            lst_Acc_clfs[i].append(acc_clf)

            lst_tpr[i].append(
                np.sum((y_test_pred.ravel() == 1) * (y_test.ravel() == 1))
                / np.sum((y_test_pred.ravel() == 1))
            )
            lst_tnr[i].append(
                np.sum((y_test_pred.ravel() == 0) * (y_test.ravel() == 0))
                / np.sum((y_test_pred.ravel() == 0))
            )

            lst_tpr_S0[i].append(
                np.sum(
                    (y_test_pred.ravel() == 1)
                    * (y_test.ravel() == 1)
                    * (S_test.ravel() == 0)
                )
                / np.sum((y_test_pred.ravel() == 1) * (S_test.ravel() == 0))
            )
            lst_tnr_S0[i].append(
                np.sum(
                    (y_test_pred.ravel() == 0)
                    * (y_test.ravel() == 0)
                    * (S_test.ravel() == 0)
                )
                / np.sum((y_test_pred.ravel() == 0) * (S_test.ravel() == 0))
            )

            lst_tpr_S1[i].append(
                np.sum(
                    (y_test_pred.ravel() == 1)
                    * (y_test.ravel() == 1)
                    * (S_test.ravel() == 1)
                )
                / np.sum((y_test_pred.ravel() == 1) * (S_test.ravel() == 1))
            )
            lst_tnr_S1[i].append(
                np.sum(
                    (y_test_pred.ravel() == 0)
                    * (y_test.ravel() == 0)
                    * (S_test.ravel() == 1)
                )
                / np.sum((y_test_pred.ravel() == 0) * (S_test.ravel() == 1))
            )

            if printAverageConfusionMatrices == True:
                lst_CM[i] += metrics.confusion_matrix(
                    y_test.ravel(), y_test_pred.ravel(), labels=[0, 1]
                )

    # 3) show the results
    if Show_DI_boxPlotsOnly == False:
        fig = plt.figure(figsize=(18, 5))

        # 3.1) D.I.
        plt.subplot(121)
        data = [np.array(lst_DI_Ref)]
        ticks_nb = [1]
        ticks_names = ["Ref"]
        for i in range(len(list_classifiers)):
            data.append(np.array(lst_DI_clfs[i]))
            ticks_nb.append(i + 2)
            ticks_names.append(list_classifierNames[i])
        plt.boxplot(data)
        plt.xticks(np.array(ticks_nb), ticks_names)
        plt.title("Disparate Impact")

        # 3.2) accuracy
        plt.subplot(122)
        data = []
        ticks_nb = []
        ticks_names = []
        for i in range(len(list_classifiers)):
            data.append(np.array(lst_Acc_clfs[i]))
            ticks_nb.append(i + 1)
            ticks_names.append(list_classifierNames[i])
        plt.boxplot(data)
        plt.xticks(np.array(ticks_nb), ticks_names)
        plt.title("Accuracy")
        # plt.savefig(PrefixFigNames+'_Boxplots.pdf')
        plt.show()

    else:
        # 3.3) ranked D.I.
        fig = plt.figure(figsize=(18, 5))

        averageAcc = []
        for i in range(len(list_classifierNames)):
            averageAcc.append(np.mean(np.array(lst_Acc_clfs[i])))
        ranksAcc = np.array(averageAcc).argsort()

        averageDI_in_Data = np.mean(np.array(lst_DI_Ref))

        data = []
        ticks_nb = []
        ticks_names = []
        for i in range(len(list_classifiers)):
            data.append(np.array(lst_DI_clfs[ranksAcc[i]]))
            ticks_nb.append(i + 1)
            meanAccLoc = np.round(np.mean(np.array(lst_Acc_clfs[ranksAcc[i]])), 4)
            ticks_names.append(
                list_classifierNames[ranksAcc[i]] + "\n\nAcc=" + str(meanAccLoc)
            )
        plt.boxplot(data)
        plt.plot(
            [0.5, len(list_classifiers) + 0.5],
            [averageDI_in_Data, averageDI_in_Data],
            "b--",
        )
        plt.text(0.51, averageDI_in_Data - 0.03, "D.I. in the test data", color="b")
        plt.xticks(np.array(ticks_nb), ticks_names)
        plt.title("Disparate Impact")
        # plt.savefig(PrefixFigNames+'_Boxplots.pdf')
        plt.show()

    # 3.4) ROC curves
    fig = plt.figure(figsize=(18, 5))
    plt.subplot(131)
    listColors = [
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
        "tab:pink",
        "tab:gray",
        "tab:olive",
        "tab:cyan",
        "lime",
        "aquamarine",
    ]
    listMarkers = ["+", "*", "X", ".", "^", "o", "v", "8", "s", "d", "H", "s"]
    plt.plot([0.0, 1.0], [0.0, 1.0], "b--")
    for i in range(len(list_classifiers)):
        plt.scatter(
            lst_tnr[i],
            lst_tpr[i],
            alpha=0.5,
            c=listColors[i],
            marker=listMarkers[i],
            s=100.0,
            label=list_classifierNames[i],
            edgecolors="none",
        )
    plt.xlabel("True negative rate")
    plt.ylabel("True positive rate")
    plt.xlim(left=0.4, right=1)
    plt.ylim(bottom=0.4, top=1)
    plt.grid()
    plt.legend(loc="upper left")

    plt.subplot(132)
    listColors = [
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
        "tab:pink",
        "tab:gray",
        "tab:olive",
        "tab:cyan",
        "lime",
        "aquamarine",
    ]
    listMarkers = ["+", "*", "X", ".", "^", "o", "v", "8", "s", "d", "H", "s"]
    plt.plot([0.0, 1.0], [0.0, 1.0], "b--")
    for i in range(len(list_classifiers)):
        plt.scatter(
            lst_tnr_S0[i],
            lst_tpr_S0[i],
            alpha=0.5,
            c=listColors[i],
            marker=listMarkers[i],
            s=100.0,
            label=list_classifierNames[i],
            edgecolors="none",
        )
    plt.xlabel("True negative rate (S=0)")
    plt.ylabel("True positive rate (S=0)")
    plt.xlim(left=0.4, right=1)
    plt.ylim(bottom=0.4, top=1)
    plt.grid()
    plt.legend(loc="upper left")

    plt.subplot(133)
    listColors = [
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
        "tab:pink",
        "tab:gray",
        "tab:olive",
        "tab:cyan",
        "lime",
        "aquamarine",
    ]
    listMarkers = ["+", "*", "X", ".", "^", "o", "v", "8", "s", "d", "H", "s"]
    plt.plot([0.0, 1.0], [0.0, 1.0], "b--")
    for i in range(len(list_classifiers)):
        plt.scatter(
            lst_tnr_S1[i],
            lst_tpr_S1[i],
            alpha=0.5,
            c=listColors[i],
            marker=listMarkers[i],
            s=100.0,
            label=list_classifierNames[i],
            edgecolors="none",
        )
    plt.xlabel("True negative rate (S=1)")
    plt.ylabel("True positive rate (S=1)")
    plt.xlim(left=0.4, right=1)
    plt.ylim(bottom=0.4, top=1)
    plt.grid()
    plt.legend(loc="upper left")
    # plt.savefig(PrefixFigNames+'_ROC.pdf')
    plt.show()

    for i in range(len(list_classifiers)):
        print("Average rates " + list_classifierNames[i] + ":")
        print(
            " -> True positive (all/S=0/S=1):",
            np.round(np.mean(np.array(lst_tpr[i])), 2),
            np.round(np.mean(np.array(lst_tpr_S0[i])), 2),
            np.round(np.mean(np.array(lst_tpr_S1[i])), 2),
        )
        print(
            " -> True negative (all/S=0/S=1):",
            np.round(np.mean(np.array(lst_tnr[i])), 2),
            np.round(np.mean(np.array(lst_tnr_S0[i])), 2),
            np.round(np.mean(np.array(lst_tnr_S1[i])), 2),
        )

    # 3.5) average results and confuction matrices
    if printAverageRes == True:
        print("Average D.I. (Average Acc):")
        for i in range(len(list_classifiers)):
            print(
                list_classifierNames[i]
                + ": "
                + str(np.round(np.mean(np.array(lst_DI_clfs[i])), 3))
                + "("
                + str(np.round(np.mean(np.array(lst_Acc_clfs[i])), 3))
                + ")"
            )

    if printAverageConfusionMatrices == True:
        print("Average confusion matrices:")
        for i in range(len(list_classifiers)):
            print(list_classifierNames[i] + ": ")
            print(lst_CM[i] / lst_CM[i].sum())
            print("")


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Clf_with_BestPredForTheSV
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import copy


class Clf_with_BestPredForTheSV:
    """
    Extension of the classifier ref_clf. When making a prediction for
    a given X_test, the prediction will be made for X_test itself and
    X_test on which the labels of the sensitive variable are swapped.
    The best of these two predictions will be returned for each
    observation.

    * This class is initiated with:
      -> A sklearn classifier (or assimilated)
      -> The column of X representing the sensitive variable. This
         column must contain labels.

    * As in sklearn, the fit method is used to fit X and y.

    * As in sklearn, the predict method will used to predict y
    on new observations have the same structure as X.
    """

    def __init__(self, ref_clf, col_S_in_X):
        """
        Initiate the model
        """
        try:
            self.ref_clf = sk.clone(ref_clf)  # should work for any sklearn classifier
        except:
            self.ref_clf = copy.deepcopy(ref_clf)  # should work for pytorch classifiers
        self.col_S_in_X = col_S_in_X

    def fit(self, X, y):
        """
        Initiate the model and fit if
        """
        self.ref_clf.fit(X, y.ravel())

    def predict(self, X_test):
        """
        Perform a prediction as in sklearn but with the best label for the S.V.
        """
        X_test_swp_SV = X_test.copy()
        swp_SV = 1.0 - X_test_swp_SV[:, self.col_S_in_X]
        X_test_swp_SV[:, self.col_S_in_X] = swp_SV

        y_test_pred = self.ref_clf.predict(X_test)
        y_test_pred_swp_SV = self.ref_clf.predict(X_test_swp_SV)

        return np.maximum(y_test_pred, y_test_pred_swp_SV)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Clf_with_ClassSpecDecRules
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Clf_with_ClassSpecDecRules:
    """
    Extension of the classifier ref_clf for which the parameters
    learnt will be specific to each class of the sensitive variable
    (e.g. different logistic regression weights are learnt for
    males and females). The predictions will naturally depend on the
    class of the sensitive variable. The best prediction may be
    optionnaly returned.

    * This class is initiated with:
      -> A sklearn classifier (or assimilated)
      -> The column of X representing the sensitive variable. This
         column must contain labels (the structure of X_train and
         X_test in the fit and predict methods must be coherent
         with this choice).
      -> ReturnBestPred (=False) to optionally return the best
      prediction.

    * As in sklearn, the fit method is used to fit X and y.

    * As in sklearn, the predict method will used to predict y
    on new observations have the same structure as X.
    """

    def __init__(self, ref_clf, col_S_in_X, ReturnBestPred=False):
        """
        Initiate the model
        """
        self.ref_clf = ref_clf
        self.col_S_in_X = col_S_in_X
        self.ReturnBestPred = ReturnBestPred

    def fit(self, X, y, verbose=False):
        """
        Initiate the model and fit it
        """

        # extract the sensitive variable and its classes
        S = X[:, self.col_S_in_X].ravel()
        self.S_classes = set(S)
        if verbose == True:
            print("Classes found in S: ", self.S_classes)

        # remove the sensitive variable from X
        X_wo_SV = X.copy()
        # X_wo_SV=np.delete(X_wo_SV,self.col_S_in_X,axis=1)

        # instantiate and train class-specific classifiers
        self.DictClassSpec_Clfs = {}
        for classLabel in self.S_classes:
            if verbose == True:
                print("Instanciate and train the model for class " + str(classLabel))
            try:
                self.DictClassSpec_Clfs[classLabel] = sk.clone(
                    self.ref_clf
                )  # should work for any sklearn classifier
            except:
                self.DictClassSpec_Clfs[classLabel] = copy.deepcopy(
                    self.ref_clf
                )  # should work for pytorch classifiers
            X_filtered = X_wo_SV[S == classLabel, :]
            y_filtered = y[S == classLabel]
            self.DictClassSpec_Clfs[classLabel].fit(X_filtered, y_filtered.ravel())

        if verbose == True:
            print("Done")

    def predict(self, X_test):
        """
        Perform a prediction as in sklearn

        If the option ReturnBestModel is false then each y is predicted
        using the model corresponding to the value of the corresponding
        sensitive variable. If true, the best y using all possible
        labels of the sensitive variable is returned.
        """

        # remove the sensitive variable from X_test
        S_tst = X_test[:, self.col_S_in_X].ravel()
        X_wo_SV = X_test.copy()
        # X_wo_SV=np.delete(X_wo_SV,self.col_S_in_X,axis=1)

        # perform the predictions for each class-specific-classifier
        self.DictClassSpec_y_pred = {}
        for classLabel in self.S_classes:
            self.DictClassSpec_y_pred[classLabel] = self.DictClassSpec_Clfs[
                classLabel
            ].predict(X_wo_SV)

        # aggregate the predictions
        y_pred = np.zeros(X_test.shape[0])
        if self.ReturnBestPred == False:
            for i in range(X_test.shape[0]):  # could be parallelized for sure
                y_pred[i] = self.DictClassSpec_y_pred[S_tst[i]][i]
        else:
            for i in range(X_test.shape[0]):
                for classLabel in self.S_classes:
                    if self.DictClassSpec_y_pred[classLabel][i] > y_pred[i]:
                        y_pred[i] = self.DictClassSpec_y_pred[classLabel][i]

        return y_pred


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Clf_with_AdaptiveThreshForS0
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class Clf_with_AdaptiveThreshForS0:
    """
    Extension of the classifier ref_clf for which the threshold
    to get y=1 is potentially adapted on the class S=0. The
    threshold will be adapted when the D.I. is below 0.8, in order
    to make it close to 0.8.

    * This class is initiated with:
      -> A sklearn classifier (or assimilated)
      -> The column of X representing the sensitive variable. This
         column must contain labels (the structure of X_train and
         X_test in the fit and predict methods must be coherent
         with this choice).

    * As in sklearn, the fit method is used to fit X and y.

    * As in sklearn, the predict method will used to predict y
    on new observations have the same structure as X.
    """

    def __init__(self, ref_clf, col_S_in_X, AdaptOnTestSet=False, DI_to_reach=0.8):
        """
        Initiate the model
        """
        try:
            self.ref_clf = sk.clone(ref_clf)  # should work for any sklearn classifier
        except:
            self.ref_clf = copy.deepcopy(ref_clf)  # should work for pytorch classifiers
        self.col_S_in_X = col_S_in_X
        self.AdaptOnTestSet = AdaptOnTestSet
        self.threshForS0 = 0.5
        self.DI_to_reach = DI_to_reach

    def _cpt_y_loc_pred(self, X_loc, S_loc):
        y_loc_pred_probaEq0 = self.ref_clf.predict_proba(X_loc)[:, 0]

        y_loc_pred__S_eq_0 = 1 * (y_loc_pred_probaEq0 < self.threshForS0)
        y_loc_pred = 1 * (y_loc_pred_probaEq0 < 0.5)  # for S=1 in the end
        for i in range(X_loc.shape[0]):
            if S_loc[i] < 0.5:
                y_loc_pred[i] = y_loc_pred__S_eq_0[i]
        return y_loc_pred

    def _adaptThresh(self, X_loc):
        S_loc = X_loc[:, self.col_S_in_X].ravel()

        y_loc_pred = self._cpt_y_loc_pred(X_loc, S_loc)
        DI_clf = cptDI(S_loc.ravel(), y_loc_pred.ravel())

        if DI_clf > self.DI_to_reach:
            # print(" -> Threshold not changed as DI ="+str(DI_clf))
            DI_clf_init = DI_clf
        else:
            DI_clf_init = DI_clf
            shift = 0.25
            iteration = 0
            Finished = False
            self.threshForS0 = 0.5
            while Finished == False:
                # ... update the threshold
                if DI_clf < self.DI_to_reach:
                    PrevThreshForS0 = self.threshForS0
                    self.threshForS0 += shift
                else:
                    PrevThreshForS0 = self.threshForS0
                    self.threshForS0 -= shift
                shift /= 2.0

                # ... compute the new D.I.
                y_loc_pred = self._cpt_y_loc_pred(X_loc, S_loc)
                DI_clf = cptDI(S_loc.ravel(), y_loc_pred.ravel())

                # ... manage the end of the lood
                iteration += 1
                if iteration > 10:
                    Finished = True
                if np.isnan(DI_clf) or DI_clf > 1.2 or DI_clf < 0:
                    Finished = True
                    self.threshForS0 = PrevThreshForS0
                    y_loc_pred = self._cpt_y_loc_pred(X_loc, S_loc)
                    DI_clf = cptDI(S_loc.ravel(), y_loc_pred.ravel())

            # print(" -> Threshold changed to: "+str(self.threshForS0)+". The D.I was "+str(DI_clf_init)+" and is now "+str(DI_clf)+".")

    def fit(self, X, y):
        """
        Initiate the model and fit if
        """
        # 1) learn the classifier
        self.ref_clf.fit(X, y.ravel())

        # 2) find the optimal threshold
        # print('Fit')
        self._adaptThresh(X)

    def predict(self, X_test):
        """
        Perform a prediction as in sklearn but with potentially adapted threshold for S=0
        """
        # eventually adapt threshForS0
        if self.AdaptOnTestSet == True:
            # print('Pred')
            self._adaptThresh(X_test)

        # compute the proba to have Y=0
        y_test_pred_probas = self.ref_clf.predict_proba(X_test)
        y_test_pred_probaEq0 = y_test_pred_probas[:, 0]

        # threshold this probability
        y_test_pred_S0 = 1 * (y_test_pred_probaEq0 < self.threshForS0)
        y_test_pred_S1 = 1 * (y_test_pred_probaEq0 < 0.5)

        # merge the results in the two groups
        S_test = X_test[:, self.col_S_in_X].ravel()
        y_test_pred = y_test_pred_S1.copy()
        for i in range(X_test.shape[0]):
            if S_test[i] < 0.5:
                y_test_pred[i] = y_test_pred_S0[i]

        return y_test_pred
