import sys
import requests as req
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import math
import matplotlib
import matplotlib.lines as mlines
import random
import numpy
from matplotlib import pyplot as plt
from matplotlib import patches
from matplotlib import text as mtext
import numpy as np
import math

class CurvedText(mtext.Text):
    """
    A text object that follows an arbitrary curve.
    """
    def __init__(self, x, y, text, axes, **kwargs):
        super(CurvedText, self).__init__(x[0],y[0],' ', **kwargs)

        axes.add_artist(self)

        ##saving the curve:
        self.__x = x
        self.__y = y
        self.__zorder = self.get_zorder()

        ##creating the text objects
        self.__Characters = []
        for c in text:
            if c == ' ':
                ##make this an invisible 'a':
                t = mtext.Text(0,0,'a')
                t.set_alpha(0.0)
            else:
                t = mtext.Text(0,0,c, **kwargs)

            #resetting unnecessary arguments
            t.set_ha('center')
            t.set_rotation(0)
            t.set_zorder(self.__zorder +1)

            self.__Characters.append((c,t))
            axes.add_artist(t)


    ##overloading some member functions, to assure correct functionality
    ##on update
    def set_zorder(self, zorder):
        super(CurvedText, self).set_zorder(zorder)
        self.__zorder = self.get_zorder()
        for c,t in self.__Characters:
            t.set_zorder(self.__zorder+1)

    def draw(self, renderer, *args, **kwargs):
        """
        Overload of the Text.draw() function. Do not do
        do any drawing, but update the positions and rotation
        angles of self.__Characters.
        """
        self.update_positions(renderer)

    def update_positions(self,renderer):
        """
        Update positions and rotations of the individual text elements.
        """

        #preparations

        ##determining the aspect ratio:
        ##from https://stackoverflow.com/a/42014041/2454357

        ##data limits
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        ## Axis size on figure
        figW, figH = self.axes.get_figure().get_size_inches()
        ## Ratio of display units
        _, _, w, h = self.axes.get_position().bounds
        ##final aspect ratio
        aspect = ((figW * w)/(figH * h))*(ylim[1]-ylim[0])/(xlim[1]-xlim[0])

        #points of the curve in figure coordinates:
        x_fig,y_fig = (
            np.array(l) for l in zip(*self.axes.transData.transform([
            (i,j) for i,j in zip(self.__x,self.__y)
            ]))
        )

        #point distances in figure coordinates
        x_fig_dist = (x_fig[1:]-x_fig[:-1])
        y_fig_dist = (y_fig[1:]-y_fig[:-1])
        r_fig_dist = np.sqrt(x_fig_dist**2+y_fig_dist**2)

        #arc length in figure coordinates
        l_fig = np.insert(np.cumsum(r_fig_dist),0,0)

        #angles in figure coordinates
        rads = np.arctan2((y_fig[1:] - y_fig[:-1]),(x_fig[1:] - x_fig[:-1]))
        degs = np.rad2deg(rads)


        rel_pos = 10
        for c,t in self.__Characters:
            #finding the width of c:
            t.set_rotation(0)
            t.set_va('center')
            bbox1  = t.get_window_extent(renderer=renderer)
            w = bbox1.width
            h = bbox1.height

            #ignore all letters that don't fit:
            if rel_pos+w/2 > l_fig[-1]:
                t.set_alpha(0.0)
                rel_pos += w
                continue

            elif c != ' ':
                t.set_alpha(1.0)

            #finding the two data points between which the horizontal
            #center point of the character will be situated
            #left and right indices:
            il = np.where(rel_pos+w/2 >= l_fig)[0][-1]
            ir = np.where(rel_pos+w/2 <= l_fig)[0][0]

            #if we exactly hit a data point:
            if ir == il:
                ir += 1

            #how much of the letter width was needed to find il:
            used = l_fig[il]-rel_pos
            rel_pos = l_fig[il]

            #relative distance between il and ir where the center
            #of the character will be
            fraction = (w/2-used)/r_fig_dist[il]

            ##setting the character position in data coordinates:
            ##interpolate between the two points:
            x = self.__x[il]+fraction*(self.__x[ir]-self.__x[il])
            y = self.__y[il]+fraction*(self.__y[ir]-self.__y[il])

            #getting the offset when setting correct vertical alignment
            #in data coordinates
            t.set_va(self.get_va())
            bbox2  = t.get_window_extent(renderer=renderer)

            bbox1d = self.axes.transData.inverted().transform(bbox1)
            bbox2d = self.axes.transData.inverted().transform(bbox2)
            dr = np.array(bbox2d[0]-bbox1d[0])

            #the rotation/stretch matrix
            rad = rads[il]
            rot_mat = np.array([
                [math.cos(rad), math.sin(rad)*aspect],
                [-math.sin(rad)/aspect, math.cos(rad)]
            ])

            ##computing the offset vector of the rotated character
            drp = np.dot(dr,rot_mat)

            #setting final position and rotation:
            t.set_position(np.array([x,y])+drp)
            t.set_rotation(degs[il])

            t.set_va('center')
            t.set_ha('center')

            #updating rel_pos to right edge of character
            rel_pos += w-used





def create_request(name):
    return "https://dblp.org/search/publ/api?q={}$&h=1000&f=1".format(name)


def extract_all_authors(xml_data,name):
    authors = {}
    for node in xml_data.iter():
        if node.tag == "authors":
            authors_tmp = []
            for author in node:
                authors_tmp.append(author.text)

            #Check if our author is actually in the paper
            if name in authors_tmp:
                for au in authors_tmp:
                    if au not in authors.keys():
                        authors[au] = 1
                    else :
                        authors[au] = authors[au]+1


    return authors

def draw(co_auth,name,generations,links):
    coordinates = {}
    center_x = 0
    center_y = 0
    #plt.xlim(-150,150)
    #plt.ylim(-150,150)
    plt.text(0,0,name)
    ax=plt.gca()

    coordinates[name] = [0,0]

    for g in range(1,generations+1):

        max_name = 100 * g * g
        concentric = 1
        authors = []
        n = len(co_auth[g])
        print(n)
        full_names_str = ""
        for name in co_auth[g]:
            full_names_str += "   " + name
        for i in range(0, int(len(full_names_str)/max_name) + 1):
            names_str = full_names_str[i*max_name:i*max_name+max_name]
            #names_str = ""
            #for name in names:
            #    names_str += "   " + name
            #print(names_str.strip())



            theta = np.linspace(0,2*np.pi, 100)
            #circle_x=-np.cos(np.linspace(0,2*np.pi,100))
            #circle_y=np.sin(np.linspace(0,2*np.pi,100))
            circle_x = 100+(10*(g*10)+concentric)*np.cos(theta)
            circle_y = 100+(10*(g*10)+concentric)*np.sin(theta)

            text = CurvedText(
            x = circle_x,
            y = circle_y,
            text=names_str,#'this this is a very, very long text',
            va = 'bottom',
            axes = ax, ##calls ax.add_artist in __init__
            )
            concentric += 15
            plt.plot(circle_x ,circle_y)

        #    angle = i * (360/n)
        #    t = i%10
        #    #x = center_x + (g*random.randint(g*15,g*15+25)) * math.cos(angle)
        #    #y = center_y +  (g*random.randint(g*15,g*15+25)) * math.sin(angle)
        #    x = center_x + (g*25) * math.cos(angle)
        #    y = center_y +  (g*25) * math.sin(angle)
        #    if x > y:
        #        if x > 0:
        #            x += t*3
        #        else:
        #            x -= t*3
        #    else:
        #        if y > 0:
        #            y += t*3
        #        else:
        #            y -= t*3

        #    plt.text(x,y, co_auth[g][i-1].replace(" ","\n"))
        #    coordinates[co_auth[g][i-1]] = [x,y]

    #for author in links.keys():
    #    for rel in links[author]:
    #        plt.plot([coordinates[rel][0], coordinates[author][0]],[coordinates[rel][1], coordinates[author][1]], marker='o')

    #for i in range(generations,0,-1):
    #    circle= plt.Circle((0,0), radius=i*(i*15+30),color=numpy.random.rand(3,))
    #    ax.add_patch(circle)

    plt.show()




def main(name):
    processed_author = []
    generations = 2
    all_authors = []
    co_author_by_author = {}
    author_by_gen = {}
    for i in range(0,generations+1):
        all_authors.append({})
        author_by_gen[i] = []
    # One author of the 0th generation: the one we are looking for
    author_by_gen[0] = [name]

    all_authors[0] = {name:1}
    for i in range(0,generations):
        for author_name in all_authors[i].keys():
            if author_name in processed_author:
                continue
            request = create_request(author_name)
            resp = req.get(request)
            tree = ET.fromstring(resp.text)
            new_co_auth = extract_all_authors(tree, author_name)
            for new_co in new_co_auth.keys():
                if new_co == author_name or i>0 and new_co in all_authors[i-1]:
                    continue
                if author_name not in co_author_by_author.keys():
                    co_author_by_author[author_name] = [new_co]
                else:
                    co_author_by_author[author_name].append(new_co)
                if new_co in all_authors[i+1].keys():
                    all_authors[i+1][new_co] = all_authors[i+1][new_co]+ new_co_auth[new_co]
                else :
                    all_authors[i+1][new_co] = new_co_auth[new_co]
                if new_co not in author_by_gen[i+1]:
                    author_by_gen[i+1].append(new_co)

        processed_author.append(author_name)


    print(author_by_gen)
    draw(author_by_gen,name, generations,co_author_by_author)



if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv[1])
