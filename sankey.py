import pandas as pd 
import numpy as np
import plotly.graph_objects as go
import random

#---Helper Functions------------------------------------------------------------
def gobackdf(df):
    '''
    Finds where user makes a backwards action and returns a data frame with the source (first screen) and target (second screen the user moves back to).
    '''
    gobackindex = df[df["User Flow Level"] == "Go-back"].index.tolist()
    goback = df["User_Flow"][gobackindex].tolist()
    before = df["User_Flow"][np.array(gobackindex)-1].tolist()
    gobackdf = pd.DataFrame(list(zip(before,goback)), columns=['Source', 'Target'])
    return gobackdf



def goback_list(df):
    '''
    Finds where user makes a backwards action and returns a double nested list with the source (first screen) and target (second screen the user moves back to).
    '''
  
    gobackindex = df[df["User Flow Level"] == "Go-back"].index.tolist()
    goback = df["User_Flow"][gobackindex].tolist()
    before = df["User_Flow"][np.array(gobackindex)-1].tolist()
    goback_list = [list(l) for l in zip(before,goback)]
    return goback_list


def user_flow_clean(df,starting_step):
    
    events = df["User_Flow"].unique()
    number_of_colors = len(events)
    #makes list of random colors of n
    color_n = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                for i in range(number_of_colors)]
    
    color_dictn = {events[i]: color_n[i] for i in range(len(events))}
    
    #Top number of steps in user flow
    n_steps = max(df.groupby("Respondant ID")["User_Flow"].count()) 


    valid_ids = df[df['User_Flow'] == starting_step]['Respondant ID'].unique()
    flow = df[(df['Respondant ID'].isin(valid_ids))] \
            .groupby('Respondant ID') \
            .User_Flow.agg(list) \
            .to_frame()['User_Flow'] \
            .apply(lambda x: x[x.index(starting_step): x.index(starting_step) + n_steps] ) \
            .to_frame() \
            ['User_Flow'].apply(pd.Series).fillna('End')


    for i, col in enumerate(flow.columns):
        flow[col] = '{}: '.format(i + 1) + flow[col].astype(str)

    flow = flow.groupby(list(range(n_steps))) \
            .size() \
            .to_frame() \
            .rename({0: 'Flow Count'}, axis=1) \
            .reset_index() \
    

    cat_cols = flow.columns[:-1].values.tolist()
    for i in range(len(cat_cols) - 1):
        if i == 0:
            source_target_df = flow[[cat_cols[i], cat_cols[i + 1], 'Flow Count']]
            source_target_df.columns = ['source', 'target', 'Flow Count']
        else:
            temp_df = flow[[cat_cols[i], cat_cols[i + 1], 'Flow Count']]
            temp_df.columns = ['source', 'target', 'Flow Count']
            source_target_df = pd.concat([source_target_df, temp_df])
        source_target_df = source_target_df.groupby(['source', 'target']).agg({'Flow Count': 'sum'}).reset_index()

        # filter out the end step
        source_target_df = source_target_df[(~source_target_df['source'].str.contains('End')) &
                                            (~source_target_df['target'].str.contains('End'))]

    # create the nodes labels list
    label_target = list(set(source_target_df.target.tolist()))
    label_source = list(set(source_target_df.source.tolist()))
    label_list = list(set(label_target + label_source))


    # create a list of colours for the nodes
    colors_node = []
    for i in label_list:
        for key, val in color_dictn.items():
            if i.find(key) > 0:
                colors_node.append(val)

    # create a list of colours for the links
    
    goback_df = gobackdf(df)
    colors_link = []
    for i in range(len(source_target_df)):
        h = False
        for j in range(len(goback_df)):
            if (source_target_df.iloc[i]["source"].find(goback_df.iloc[j]["Source"]) > 0) and (source_target_df.iloc[i]["target"].find(goback_df.iloc[j]["Target"]) > 0):
                colors_link.append("#ff4f4b")
                h = True
                break
            else:
                continue
        if h == False:
            colors_link.append("rgba(136, 157, 179 0.5)")

    # add index for source-target pair
    source_target_df['source_id'] = source_target_df['source'].apply(lambda x: label_list.index(x))
    source_target_df['target_id'] = source_target_df['target'].apply(lambda x: label_list.index(x))
    
    return source_target_df,label_list,flow,colors_node,colors_link

#---Main Plotting Function--------------------------------------------------------------------------------------------------------

def user_sankey(df):
    '''
    Main function that will plot the user flow and print facts like unique flows, most used flow, max steps, min steps. Will also return data frame of all flows, each column being a step
    '''
    source_target_df,label_list,flow,colors_node,colors_link = user_flow_clean(df,"Profile")
    
    layout = dict(
        height=400,
        width=5000,
        margin=dict(t=50, l=0, r=0, b=50),
        title="User Flows",
        font=dict(
            size=16,
            
        ) )

    fig = go.Figure(data = [go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            color=colors_node,
            line=dict(
                color="black",
                width=0.5
            ),
            label=label_list
        ),
        link=dict(
            source=source_target_df['source_id'].values.tolist(),
            target=source_target_df['target_id'].values.tolist(),
            value=source_target_df['Flow Count'].astype(int).values.tolist(),
            color = colors_link,
            hoverlabel=dict(
                bgcolor='#C24c77')
        )
    )] , layout = layout)



    fig.show()
    
    print ("- There were " + str(len(flow)) + " unique user flows")
    print (("- The most used flow was used by ") + str(max(flow["Flow Count"])) + (" participants")) 
    print ("- The maximum number of steps it took users to complete the task was "+ str(len(flow.columns)-1) )
    
    print ( "- The minimum number of steps it took users to complete the task was " + str(flow.columns[flow.astype(str).apply(lambda x: x.str.contains('End')).any()].tolist()[0]))


    
    return flow
    