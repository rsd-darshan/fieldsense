# Model card: fertilizer recommendation

## Model type

scikit-learn classifier with encoded categorical variables.

## Inputs

`temperature`, `humidity`, `moisture`, `soil_type`, `crop_type`, `nitrogen`, `potassium`, `phosphorous`

## Output

Predicted fertilizer class label.

## Evaluation (to fill)

- Accuracy:
- Macro F1:
- Confusion matrix path:

## Limitations

- Categorical encoding assumes closed-world label sets.
- May underperform for unseen soil/crop combinations.
