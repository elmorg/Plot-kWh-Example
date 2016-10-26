from __future__ import print_function
from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import DatetimeTickFormatter, HoverTool, Label, LabelSet, ColumnDataSource, CustomJS, Circle, Legend, Button, Range1d
from bokeh.layouts import column, widgetbox, layout, row
from bokeh.models.widgets import CheckboxGroup, DatePicker, Slider, RadioGroup
from bokeh.resources import CDN
from bokeh.embed import autoload_static, autoload_server
from bokeh.client import push_session
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from bokeh.palettes import small_palettes
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

# NOTES:
# - use this to convert to day of year: print(daily14.index[0].timetuple().tm_yday)
# - to concatenate: daily = pd.concat([df.loc[:,'DayNum'] , df.loc[:,'0.5':'24'].apply(np.sum, axis =1)],axis=1)
# - set column names: daily.columns = ['Day']


def totimestamp(dt, epoch=datetime(1970,1,1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6

def getHourlyAvg(allData):
    # Get mean hourly values for each weekday
    hourlyAvg = allData.loc[allData.Day == 1,'00:30':'00:00'].apply(np.mean, axis =0)
    for d in range(2,8):
        hourlyAvg = pd.concat([hourlyAvg,allData.loc[allData.Day == d,'00:30':'00:00'].apply(np.mean, axis =0)],axis=1)
    allstd = allData.loc[:,'00:30':'00:00'].apply(np.std, axis =0)
    hourlyAvg = pd.concat([hourlyAvg,allstd],axis=1)
    return hourlyAvg

MonthTimestamps = [totimestamp(datetime(2000,01,01))*1000,
                   totimestamp(datetime(2000,02,01))*1000,
                   totimestamp(datetime(2000,03,01))*1000,
                   totimestamp(datetime(2000,04,01))*1000,
                   totimestamp(datetime(2000,05,01))*1000,
                   totimestamp(datetime(2000,06,01))*1000,
                   totimestamp(datetime(2000,07,01))*1000,
                   totimestamp(datetime(2000,8,01))*1000,
                   totimestamp(datetime(2000,9,01))*1000,
                   totimestamp(datetime(2000,10,01))*1000,
                   totimestamp(datetime(2000,11,01))*1000,
                   totimestamp(datetime(2000,12,01))*1000,
                   totimestamp(datetime(2001,01,01))*1000]

plotWidth = 900
plotHeight = 350
# Read in data:
df = pd.read_csv(dir_path + '/Data/AR_alldata.csv', index_col=0, parse_dates=True,dayfirst=True)
numWeeks = len(df.loc[df.Day == 1,'Day']) # get the total number of weeks of data
maxVal = df.loc[:,'00:30':'00:00'].max(axis = 0).max(axis = 0) # get the maximum value of the data
cols = list(df.columns.values) # Get column names
times = cols[2:len(cols)] # extract time values
xlabel = pd.Series(pd.to_datetime(times, format = '%H:%M'))
xlabel.loc[len(xlabel)-1] += timedelta(days=1) # convert last time (00:00) to next day

hourly = ColumnDataSource(data=dict(Time = xlabel,
                                    mon = [],
                                    tue = [],
                                    wed = [],
                                    thu = [],
                                    fri = [],
                                    sat = [],
                                    sun = [],
                                    std = [],
                                    TLabel = times
                                    ))

# Create table of sum total daily readings
daily = df.loc[:,'00:30':'00:00'].apply(np.sum, axis =1)
# Segment data according to year
daily14 = daily.loc[(daily.index >=  '20140101') & (daily.index <  '20150101')]
daily15 = daily.loc[(daily.index >=  '20150101') & (daily.index <  '20160101')]
daily16 = daily.loc[(daily.index >=  '20160101') & (daily.index <  '20170101')]

d14 = ColumnDataSource(pd.DataFrame({'Date': daily14.index.map(lambda t: t.replace(year=2000)),
                                    'Value': daily14.values,
                                    'DLabel': daily14.index.map(lambda t: t.strftime(format = '%d/%m'))}))
d15 = ColumnDataSource(pd.DataFrame({'Date': daily15.index.map(lambda t: t.replace(year=2000)),
                                    'Value': daily15.values,
                                    'DLabel': daily15.index.map(lambda t: t.strftime(format = '%d/%m'))}))
d16 = ColumnDataSource(pd.DataFrame({'Date': daily16.index.map(lambda t: t.replace(year=2000)),
                                    'Value': daily16.values,
                                    'DLabel': daily16.index.map(lambda t: t.strftime(format = '%d/%m'))}))

# create HOURLY plot
p1 = figure(title="Half Hourly Electricity Use", x_axis_label='Time (h)',
            y_axis_label='kWh',x_axis_type="datetime",tools="pan,box_zoom,wheel_zoom,reset,save",
            x_range=Range1d(totimestamp(xlabel.iloc[0])*1000, totimestamp(xlabel.iloc[len(xlabel)-1])*1000),
            y_range=Range1d(0,maxVal))
p1.plot_height = plotHeight
p1.plot_width = plotWidth
p1.toolbar_location="above"
# add a line renderer with legend and line thickness

l_mon = p1.line(x='Time', y= 'mon', source = hourly, line_width=2,line_color = small_palettes['Dark2'][6][0])
l_tue = p1.line(x='Time', y= 'tue', source = hourly, line_width=2,line_color = small_palettes['Dark2'][6][1])
l_wed = p1.line(x='Time', y= 'wed', source = hourly, line_width=2,line_color = small_palettes['Dark2'][6][2])
l_thu = p1.line(x='Time', y= 'thu', source = hourly, line_width=2,line_color = small_palettes['Dark2'][6][3])
l_fri = p1.line(x='Time', y= 'fri', source = hourly, line_width=2,line_color = small_palettes['Dark2'][6][4])
l_sat = p1.line(x='Time', y= 'sat', source = hourly, line_width=2,line_color = small_palettes['Dark2'][6][5])
l_sun = p1.line(x='Time', y= 'sun', source = hourly, line_width=2,line_color = small_palettes['Dark2'][8][7])
l_std = p1.line(x='Time', y= 'std', source = hourly, line_width=2,line_color = 'black',line_dash = 'dashed')

# create DAILY plot
p2 = figure(title="Daily Electricity Use", x_axis_label='Date',
            y_axis_label='kWh', x_axis_type="datetime",tools="pan,box_zoom,wheel_zoom,reset,save",
            x_range=Range1d(totimestamp(datetime(2000,01,01))*1000, totimestamp(datetime(2000,12,31))*1000))
p2.plot_height = plotHeight
p2.plot_width = plotWidth
p2.toolbar_location="above"
# add a line renderer with legend and line thickness
l_14 = p2.line(x = 'Date', y = 'Value', source = d14, line_width=2,line_color = small_palettes['PuBu'][3][0])
l_15 = p2.line(x = 'Date', y = 'Value', source = d15, line_width=2,line_color = small_palettes['PuRd'][3][0])
l_16 = p2.line(x = 'Date', y = 'Value', source = d16, line_width=2,line_color = small_palettes['YlGn'][3][0])


p1.add_tools(HoverTool(tooltips=[("Time","@TLabel")], mode='mouse', line_policy = 'nearest'))
p2.add_tools(HoverTool(tooltips=[("Date","@DLabel")], mode='mouse', line_policy = 'nearest',
                       point_policy= 'snap_to_data',show_arrow = False ,anchor = 'top_left'))

checkbox1 = CheckboxGroup(
                          labels=["", "", "",
                                  "", "", "", "",""], active=[0,1,2,3,4,5,6,7,8], sizing_mode = 'scale_both',width = 200,height = 200)
checkbox1.height = 200
checkbox1.callback = CustomJS.from_coffeescript(args=dict(l0=l_mon, l1=l_tue, l2=l_wed, l3=l_thu,
                                        l4=l_fri, l5=l_sat, l6=l_sun, l7=l_std, checkbox=checkbox1),
                              code="""
                                  l0.visible = 0 in checkbox.active;
                                  l1.visible = 1 in checkbox.active;
                                  l2.visible = 2 in checkbox.active;
                                  l3.visible = 3 in checkbox.active;
                                  l4.visible = 4 in checkbox.active;
                                  l5.visible = 5 in checkbox.active;
                                  l6.visible = 6 in checkbox.active;
                                  l7.visible = 7 in checkbox.active;
                                  """)


checkbox2 = CheckboxGroup(
                          labels=["", "", ""], active=[0, 1,2])
checkbox2.callback = CustomJS.from_coffeescript(args=dict(l0=l_14, l1=l_15, l2=l_16, checkbox=checkbox2),
                              code="""
                                  l0.visible = 0 in checkbox.active;
                                  l1.visible = 1 in checkbox.active;
                                  l2.visible = 2 in checkbox.active;
                                  """)

datePickStart = DatePicker(name = "StartD",title = "Start Date:",max_date = date(2016, 11, 01),
                           min_date = date(2014, 01, 01),value = date(2014, 01, 01),width = 180)

datePickEnd = DatePicker(name = "EndD",title = "End Date:",max_date = date(2016, 11, 01),
                         min_date = date(2014, 01, 01),value = date(2016, 11, 01),width = 180)



def dateChange():
    dateVal_start = datePickStart.value
    dateStr_start = dateVal_start.strftime(format = '%Y%m%d')
    dateVal_end = datePickEnd.value
    dateStr_end = dateVal_end.strftime(format = '%Y%m%d')
    df2 = df.loc[(df.index >=  dateStr_start) & (df.index <=  dateStr_end)]
    hourlyAvg = getHourlyAvg(df2)
    p1.title.text = "Half Hourly Electricity Use: " + dateVal_start.strftime(format = '%d/%m/%y') + \
        " - " + dateVal_end.strftime(format = '%d/%m/%y')
    hourly.data = dict(Time = xlabel,
                       mon = hourlyAvg.iloc[:,0],
                       tue = hourlyAvg.iloc[:,1],
                       wed = hourlyAvg.iloc[:,2],
                       thu = hourlyAvg.iloc[:,3],
                       fri = hourlyAvg.iloc[:,4],
                       sat = hourlyAvg.iloc[:,5],
                       sun = hourlyAvg.iloc[:,6],
                       std = hourlyAvg.iloc[:,7],
                       TLabel = times
                       )

def weekChange(attr,old,new):
    dateVal_start = mondays.index[new-1]
    dateStr_start = dateVal_start.strftime(format = '%Y%m%d')
    dateVal_end = dateVal_start + timedelta(days=6)
    dateStr_end = dateVal_end.strftime(format = '%Y%m%d')
    df2 = df.loc[(df.index >=  dateStr_start) & (df.index <=  dateStr_end)]
    hourlyAvg = getHourlyAvg(df2)
    p1.title.text = "Half Hourly Electricity Use: " + dateVal_start.strftime(format = '%d/%m/%y') + \
        " - " + dateVal_end.strftime(format = '%d/%m/%y')
    hourly.data = dict(Time = xlabel,
                       mon = hourlyAvg.iloc[:,0],
                       tue = hourlyAvg.iloc[:,1],
                       wed = hourlyAvg.iloc[:,2],
                       thu = hourlyAvg.iloc[:,3],
                       fri = hourlyAvg.iloc[:,4],
                       sat = hourlyAvg.iloc[:,5],
                       sun = hourlyAvg.iloc[:,6],
                       std = hourlyAvg.iloc[:,7],
                       TLabel = times
                       )


slider = Slider(start=1, end=numWeeks, value=1, step=1,title = 'Slide to select week', width = 360)
slider.on_change('value',weekChange)
button = Button(label="Plot between start and end dates")
button.on_click(dateChange)
button.width = 210

radio_group = RadioGroup(
                         labels=["Whole year","January", "February", "March", "April", "May", "June",
                                 "July", "August","September", "October", "November", "December"], active=0)

def monthSel(active):
    if active == 0:
        p2.x_range.start = MonthTimestamps[0]
        p2.x_range.end = MonthTimestamps[12]
    else :
        p2.x_range.start = MonthTimestamps[active-1]
        p2.x_range.end = MonthTimestamps[active]

radio_group.on_click(monthSel)
dPickWidget = widgetbox(button)
blank = widgetbox(radio_group,width = 400)
p1Widget = widgetbox(checkbox1)
p2Widget = widgetbox(checkbox2)
l = layout([[column(slider,row(datePickStart,datePickEnd,height=210),dPickWidget,width = 400),p1, p1Widget],[blank,p2,p2Widget]])

legend1 = Legend(legends=[
                          ("Mon",   [l_mon]),
                          ("Tue",   [l_tue]),
                          ("Wed",   [l_wed]),
                          ("Thu",   [l_thu]),
                          ("Fri",   [l_fri]),
                          ("Sat",   [l_sat]),
                          ("Sun",   [l_sun]),
                          ("Deviation",   [l_std])
                          ], location=(0, -5))


legend2 = Legend(legends=[
                          ("2014",   [l_14]),
                          ("2015",   [l_15]),
                          ("2016",   [l_16]),
                          ], location=(0, -5))

p1.add_layout(legend1, 'right')
p2.add_layout(legend2, 'right')

p1.xaxis.formatter=DatetimeTickFormatter(formats=dict(
                                                hours=["%R"],
                                                days=["%R"],
                                                months=["%R"],
                                                years=["%R"])
                                         )

p2.xaxis.formatter=DatetimeTickFormatter(formats=dict(
                                                hours=["%b"],
                                                days=["%d %b"],
                                                months=["%b"],
                                                years=["%b"])
                                         )


curdoc().add_root(l)
