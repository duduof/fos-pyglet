cimport requestLinkedList

cdef extern from "stdlib.h":
    ctypedef unsigned long size_t
    void *malloc(size_t size)
    void free(void *pointer)


# Global Variables
cdef ListNode *head = NULL
cdef ListNode *tail = NULL
cdef int numNodes = 0
cdef ListNode *iteratorPosition


cdef void createEmptyList():
    global head
    global tail
    global numNodes

    if (head != NULL):
        destroyList()

    head = <ListNode*> malloc(sizeof(ListNode))
    head.data = NULL
    head.next = NULL
    tail = head
    numNodes = 0


cdef void destroyList():
    global head
 
    if (head != NULL):
        makeEmpty( )
        free(head)
        head = NULL


cdef void makeEmpty(): 
    global head
    global tail
    global numNodes

    cdef ListNode* p = head.next
    cdef ListNode *cur
    while (p != NULL):
        if (p.data != NULL):
            free(p.data)
        cur = p
        p = p.next 
        free(cur)
    
    head.next = NULL
    tail = head
    numNodes = 0 


cdef void addLast(RequestInfo* data):
    global tail
    global numNodes

    cdef ListNode* p = <ListNode*> malloc(sizeof(ListNode))
    p.data = data
    p.next = NULL
    tail.next = p
    tail = p
    numNodes += 1
   

cdef RequestInfo* removeFirst():
    global head
    global tail
    global numNodes

    cdef ListNode* p = head.next
    cdef RequestInfo* requestInfo = NULL

    if (p != NULL):
        head.next = p.next
        requestInfo = p.data  
        free(p)
        numNodes -= 1
        if (numNodes == 0):
            head.next = NULL
            tail = head

    return requestInfo


cdef int size():
    global numNodes

    return numNodes

# The iterator should not be mixed with remove
cdef RequestInfo* first():
    global head
    global iteratorPosition

    iteratorPosition = head.next
    if (iteratorPosition != NULL):
        return iteratorPosition.data

    return NULL



cdef RequestInfo* next():
    global iteratorPosition

    if (iteratorPosition != NULL):
        iteratorPosition = iteratorPosition.next

    if (iteratorPosition != NULL):
        return iteratorPosition.data

    return NULL